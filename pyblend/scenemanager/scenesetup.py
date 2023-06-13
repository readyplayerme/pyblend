# <pep8 compliant>

import contextlib
from pathlib import Path

import bpy
from pyblend import file_io


def create_new_scene(scene_name: str = "Validation") -> bpy.types.Scene:
    """Create a new scene, name it, and make it active.

    :param scene_name: New name for the scene, defaults to 'Validation'
    :type scene_name: str, optional
    :return: The new scene object.
    :rtype: bpy.types.Scene
    """
    # We can't guarantee the name. If a scene with that name already exists, a suffix is appended. Keep a reference.
    new_scene = bpy.data.scenes.new(scene_name)
    bpy.context.window.scene = new_scene
    return new_scene


def clear_scenes(keep_scene: bpy.types.Scene | None = None) -> bpy.types.Scene:
    """Clear all scenes except the one passed as argument.

    :param keep_scene: Scene to keep, defaults to None
    :type keep_scene: bpy.types.Scene, optional
    :return: The scene that was kept.
    :rtype: bpy.types.Scene
    """
    if not keep_scene:
        keep_scene = create_new_scene()
    for scene_to_delete in bpy.data.scenes:
        if scene_to_delete is keep_scene:
            continue
        # Trying to remove the only scene left throws an error.
        with contextlib.suppress(RuntimeError):
            bpy.data.scenes.remove(scene_to_delete)
    bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)
    return keep_scene


def link_scene(filepath: str | Path, scene_name: str):
    """Link a scene from another blend-file into the currently opened project."""
    abs_path = file_io.paths.get_abs_path(filepath)
    bpy.ops.wm.append(
        filepath=abs_path.name,
        directory=f"{filepath}\\Scene\\",
        filename=scene_name,
        link=True,
        autoselect=False,
        active_collection=False,
        instance_collections=True,
    )


def unlink_scenes(scene_names: list[str]):
    """Remove a linked scene from the currently opened project."""
    for scn in scene_names:
        with contextlib.suppress(KeyError):
            bpy.data.batch_remove((bpy.data.libraries[scn],))  # This is experimental.
