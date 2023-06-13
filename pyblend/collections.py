import bpy


def get_collection(name: str = "Collection", make_new: bool = False) -> bpy.types.Collection | None:
    """Get existing blender collection by name (from scene).

    :param name: Name of the collection to look for.
    :param make_new: If it doesn't exist already, create a new collection in the scene with the given name.
    :return: The collection if it exists or is created, otherwise None.
    """
    collection = bpy.data.collections.get(name, None)
    if not collection and make_new:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
    return collection
