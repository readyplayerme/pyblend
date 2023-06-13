import contextlib
import logging
from pathlib import Path

import bpy
import numpy as np


@contextlib.contextmanager
def maintain_object_selection():
    """Restore object selection after context.

    Example:
        >>> with maintain_object_selection():
        ...     # Modify selection
        ...     bpy.ops.object.select_all(action='SELECT')
        >>> # Selection restored
    """
    previous_selection = [obj for obj in bpy.data.objects if obj.select_get()]
    active_object = bpy.context.active_object
    try:
        yield
    finally:
        if previous_selection:
            for obj in previous_selection:
                obj.select_set(True)
        else:
            bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = active_object


@contextlib.contextmanager
def maintain_object_visibility(objects: list[bpy.types.Object] | None = None):
    """Restore object viewport and render visibility after context.

    If no objects are given, all objects are used.

    Example:
        >>> with maintain_object_visibility():
        ...     # Modify visibility
        ...     bpy.context.active_object.hide_viewport = True
        >>> # Visibility restored
    """
    if objects is None:
        objects = bpy.data.objects
    previous_visibility = {obj.name: (obj.hide_viewport, obj.hide_render) for obj in objects}
    try:
        yield
    finally:
        for obj_name, (viewport, render) in previous_visibility.items():
            obj = bpy.data.objects.get(obj_name)
            if obj is None:
                continue
            obj.hide_viewport = viewport
            obj.hide_render = render


class CaptureObjects:
    """Capture objects before and after a context manager block.

    Example:
    >>> import bpy
    >>> bpy.ops.curve.primitive_bezier_circle_add()
    >>> with CaptureObjects() as cm:
    ...     # Add more objects.
    ...     bpy.ops.mesh.primitive_cube_add()
    ...     bpy.ops.object.camera_add()
    >>> # Get the difference between the objects before and after the context manager block.
    >>> print(cm.difference)
    """

    def __init__(self, type_: str | None = None):
        self.type = type_
        self.objects_before: list[bpy.types.Object] = []
        self.objects_after: list[bpy.types.Object] = []
        self.difference: list[bpy.types.Object] = []

    def __enter__(self):
        self.objects_before = self._get_objects()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.objects_after = self._get_objects()
        self.difference = list(set(self.objects_after) - set(self.objects_before))

    def _get_objects(self) -> list[bpy.types.Object]:
        if self.type is None:
            return bpy.data.objects[:]
        return [obj for obj in bpy.data.objects if obj.type == self.type]


def remove_object_from_file_by_name(name: str):
    """Remove the object with the given name from the current file.

    :param name: Name of object to remove
    :return: True if object was removed, False if object could not be found or removed.
    """
    obj = bpy.data.objects.get(name)
    return False if obj is None else remove_object_from_file(obj)


def remove_object_from_file(obj: bpy.types.Object) -> bool:
    """Remove an object from the current file.

    :param obj: Object to remove
    :return: True if object was removed, False if object could not be removed.
    """
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)

    obj.user_clear()
    if not obj.users:
        bpy.data.objects.remove(obj)
        del obj
        return True
    logging.warning(f"Object '{obj.name}' cannot be removed, still in use.")
    return False


def import_objects(
    source_path: Path | str,
    obj_type: str | None = None,
    include: list[str] | None = None,
    link: bool = True,
    relative: bool = True,
) -> list[bpy.types.Object]:
    """Link objects from an external blend file to the current scene.

    :param source_path: File path to blend file from which to link objects from.
    :param obj_type: What type of objects to link, all types if set to None, defaults to None.
    :param include: List of names to include in import. Inclide all if set to None, defaults to None.
    :param link: Link objects instead of appending, defaults to True.
    :param relative: Set links as relative paths, defaults to True.
    :return: List of linked objects.
    """
    with CaptureObjects() as captured_objects:
        with bpy.data.libraries.load(filepath=str(source_path), link=link, relative=relative) as (data_from, data_to):
            data_to.objects = include or data_from.objects
        # Link only objects that match our criteria. Objects that weren't found by name are None.
        objects = list(filter(lambda obj: obj and obj.type == obj_type or not obj_type, data_to.objects))
        for obj in objects:
            try:
                bpy.context.scene.collection.objects.link(obj)
            except (RuntimeError, TypeError, AttributeError) as error:
                logging.error(error)
                continue
    # For reasons unknown, the armature is improted nonetheless from the source path. Get rid of it.
    uninvited_objects = set(captured_objects.difference) - set(objects)
    for obj in uninvited_objects:
        remove_object_from_file(obj)
    return objects


def unlink_object(obj: bpy.types.Object) -> bool:
    """Unlink an object from the file.

    If object is not linked to the file, it will be skipped.

    :param objects: Linked objects to remove.
    :return: True if object was unlinked, False if object could not be unlinked.
    """
    try:
        bpy.data.libraries.remove(obj.library)
        return True
    except TypeError:
        logging.warning(f"Unlinking '{obj.name}' failed. Object is not linked. Skipping.")
        return False


def unlink_objects(objects: list[bpy.types.Object], type_: str | None = None) -> bool:
    """Unlink objects from the file.

    If objects are not linked to the file, they will be skipped.

    :param objects: Linked objects to remove.
    :param type_: Type of objects to remove, all types if None, defaults to None.
    :return: True if all objects were unlinked or objects is empty, False if one or more objects could not be unlinked.
    """
    ret = True
    for obj in objects:
        if obj.type == type_ or type_ is None:
            ret &= unlink_object(obj)
    return ret


def get_mesh_objects() -> list[bpy.types.Object]:
    """Get all mesh objects in the file."""
    return [obj for obj in bpy.data.objects if obj.type == "MESH"]


def get_skinned_mesh_objects():
    """Get all objects with an armature modifier."""
    skinned_objects = []
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            skinned_objects.extend(obj for mod in obj.modifiers if mod.type == "ARMATURE")
    return skinned_objects


def get_vertices_positions(context: bpy.types.Context, obj: bpy.types.Object) -> np.ndarray:
    """Get positions of vertices for the evaluated object, including modifiers.

    :param context: Blender's current context.
    :param obj: Object from which to get evaluated vertex positions.
    :return: Evaluated positions of vertices.
    """
    # Get the evaluated version of the object with modifiers applied.
    deps_graph = context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(deps_graph)
    # Extract positions of vertices.
    mesh = eval_obj.to_mesh()
    vertices = mesh.vertices
    n_vertices = len(vertices)
    positions = np.empty(n_vertices * 3)
    vertices.foreach_get("co", positions)
    positions = positions.reshape(n_vertices, 3)  # Not really necessary, but more intuitive.
    # Cleanup.
    eval_obj.to_mesh_clear()
    del mesh, vertices
    return positions


def move_modifier_to_top(obj: bpy.types.Object, modifier_name: str):
    """Move modifier to the top of the stack.

    :param obj: Object that has the modifier in its stack.
    :param modifier_name: Name of modifier to move.
    """
    try:
        mod = obj.modifiers[modifier_name]
    except KeyError:
        logging.warning(f"Modifier '{modifier_name}' not found in object '{obj.name}'.")
        return
    while obj.modifiers.find(mod.name) != 0:
        with bpy.context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_move_up(modifier=mod.name)


def add_color_attribute(mesh: bpy.types.Mesh, name: str) -> bpy.types.FloatColorAttribute:
    """Add color attribute if it doesn't exist and make active."""
    if name in mesh.color_attributes:
        attr = mesh.color_attributes[name]
    else:
        attr = mesh.color_attributes.new(name, "FLOAT_COLOR", "POINT")
    mesh.color_attributes.active_color = attr
    return attr


def bake_ambient_occlusion_vtx(obj: bpy.types.Object, attribute_name: str = "AO") -> bool:
    """Bake ambient occlusion to vertex colors attribute.

    :param obj: Object to bake ambient occlusion to.
    :param attribute_name: Name of vertex color attribute to bake to, defaults to "AO".
    :return: True if baking was successful, False if baking failed.
    """
    bpy.data.scenes["Scene"].render.engine = "CYCLES"
    bpy.data.scenes["Scene"].cycles.bake_type = "AO"
    bpy.data.scenes["Scene"].render.bake.target = "VERTEX_COLORS"
    add_color_attribute(obj.data, attribute_name)
    window = bpy.context.window_manager.windows[0]
    with bpy.context.temp_override(window=window, selected_objects=[obj], active_object=obj, object=obj):
        if bpy.ops.object.bake.poll():
            bpy.ops.object.bake(type="AO")
            return True
        logging.error(f"Ambient occlusion could not be baked for Object '{obj.name}'.")
        return False


def apply_transforms_to_delta(obj: bpy.types.Object):
    """Apply the transforms of the given object to its delta transforms."""
    # Convert the rotation to a quaternion, add it to the delta_rotation_quaternion, and then convert back to euler
    obj.delta_rotation_quaternion.rotate(obj.rotation_euler)
    obj.delta_rotation_euler = obj.delta_rotation_quaternion.to_euler("XYZ")

    obj.delta_location += obj.location
    obj.delta_scale *= obj.scale

    # Clear the object's transforms
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
