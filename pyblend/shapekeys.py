import bpy
import numpy as np
import pyblend.object
import pyblend.overrides
import pyblend.shapekeys


def add_shape_key(obj: bpy.types.Object, key_name: str) -> bpy.types.ShapeKey:
    """Create and return a new, unmodified shape key on an object.

    :param obj: Object for which to create the shape key.
    :param key_name: Name to give the new shape key.
    :return: Reference to the created shape key.
    """
    return obj.shape_key_add(name=key_name, from_mix=False)


def clear_shape_keys_weights(object: bpy.types.Object):
    """Clear shape keys weights on the source and target objects.

    :param objects: List of objects for which to clear shape keys weights.
    :type objects: List[bpy.types.Object]
    """
    try:
        for key in object.data.shape_keys.key_blocks:
            key.value = 0.0
    except AttributeError:
        print(f"Cannot clear shape key weights. No shape keys on '{object.name}'!")
    object.active_shape_key_index = 0
    object.data.update()


def set_exclusive_shape_weight(mesh: bpy.types.Mesh, key: str, weight: float = 1.0):
    """Set target shape key weight, and all others to 0."""
    try:
        mesh.shape_keys.key_blocks[key]
    except KeyError:
        print(f"Error setting shape keys: Shape key '{key}' not found in '{mesh.name}'! Skipping.")
        return
    except AttributeError:
        print(f"Error setting shape keys: Mesh '{mesh.name}' has no shape keys! Skipping.")
        return
    # foreach_set doesn't not work here, so we have to loop.
    for shape in mesh.shape_keys.key_blocks:
        shape.value = 0.0
    mesh.shape_keys.key_blocks[key].value = weight
    mesh.update()


def transfer_shape_keys(
    context: bpy.types.Context,
    src: bpy.types.Object,
    target: bpy.types.Object,
    keys: list[str] | None = None,
    base_name: str = "Basis",
):
    """Transfer shape keys from a source object to a target object.

    This function assumes the source mesh deforms the target mesh by any means.
    Previously existing shape keys a cleared from the target object.

    :param context: Blender's current context.
    :param src: Source object with shape keys.
    :type target: bpy.types.Object
    :param keys: If a list of strings are provided, only shape keys in that list will be transferred.
    """
    if not src or not target:
        return
    try:
        src_shape_keys = src.data.shape_keys.key_blocks
    except AttributeError:
        print(f"No shape-keys on mesh '{src.name}'")
        return
    target.shape_key_clear()
    pyblend.shapekeys.add_shape_key(target, base_name)
    for src_key in src_shape_keys[1:]:  # Skip basis shape key.
        if keys and src_key.name not in keys:
            continue
        target_key = add_shape_key(target, src_key.name)
        src_key.value = 1.0
        positions = pyblend.object.get_vertices_positions(context, target)
        set_shape_key_data(target_key, positions)
        src_key.value = 0.0
    target.data.shape_keys.name = target.name
    src.active_shape_key_index = 0
    target.active_shape_key_index = 0


def set_shape_key_data(shape_key: bpy.types.ShapeKey, data: np.ndarray):
    """Set the position data of a shape key.

    :param shape_key: Shape key which to modify.
    :param data: Position data for vertices.
    """
    if data.shape[0] != len(shape_key.data):
        print(f"Mismatch between position data and vertex count for shape key '{shape_key.name}'")
        return
    shape_key.data.foreach_set("co", data.flatten())
