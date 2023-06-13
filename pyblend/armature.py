import bpy
import logging


def get_first_armature(objects: list[bpy.types.Object] | None = None) -> bpy.types.Object | None:
    """Get the first armature in the scene or None.

    :param objects: List of objects to search in. If None, search through all objects in the file.
    :return: The first armature found or None.
    """
    objs = objects or list(bpy.data.objects)  # type: ignore
    return next((obj for obj in objs if obj.type == "ARMATURE"), None)  # type: ignore


def get_first_armature_modifier(obj: bpy.types.Object) -> bpy.types.ArmatureModifier | None:
    """Get the first armature modifier of the object, if any.

    :param obj: Object to get the armature modifier of.
    :return: The armature modifier of the object or None.
    """
    return next((mod for mod in obj.modifiers if mod.type == "ARMATURE"), None)


def set_armature(obj: bpy.types.Object, armature: bpy.types.Object) -> bool:
    """Parent object to armature and modify the object's armature modifier accordingly, if present.

    Return False if the object type does not support armature modifiers, or the armature is not of type ARMATURE.

    :param obj: Object to set as a child to the armature.
    :param armature: Armature to set as a parent to the object.
    :return: Whether setting the armature was successful.
    """
    if armature.type != "ARMATURE":
        return False
    mod = get_first_armature_modifier(obj) or obj.modifiers.new(name="Armature", type="ARMATURE")
    # In case the object type doesn't support armature modifiers, the modifier will be None.
    if not mod:
        return False

    obj.parent = armature
    mod.object = armature
    # Assume "Armature" is the only modifier, but the name is not safe because of counter-suffixes.
    mod.name = "Armature"
    logging.debug(f"ARMATURE: {obj.name} set to {armature.name}")
    return True


def set_armature_on_objects(objects: list[bpy.types.Object], armature: bpy.types.Object) -> bool:
    """Attach given objects to the armature.

    If the objects already have an armature, it will be replaced, and the old armature won't be deleted.

    :param objects: List of objects to attach to the armature.
    :param armature: Armature to attach the objects to.
    :return: Whether setting the armature for all objects was successful.
    """
    success = True
    for obj in objects:
        # Don't try to attach an armature to an armature.
        if obj.type == "ARMATURE":
            continue
        success &= set_armature(obj, armature)
    return success
