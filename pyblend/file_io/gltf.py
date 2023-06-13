"""This module provides file operations for glTF files."""
# <pep8 compliant>

from pathlib import Path

import bpy


def export_gltf(filepath: Path | str, **kwargs) -> tuple[bool, str]:
    """Export to a glTF file.

    It's a wrapper for the glTF add-on's export operator. It accepts the export settings as keyword arguments.

    :param filepath: Where to save the file.
    :param kwargs: Export settings.
    :return: A tuple with it's first element indicating whether export was successful, a message as the second element.
    """
    filepath = str(filepath)
    if not (filepath.lower().endswith(".glb") or filepath.lower().endswith(".gltf")):
        return (False, f"Destination file is not a glTF file: {filepath}")

    try:
        if bpy.ops.export_scene.gltf(filepath=filepath, **kwargs) == {"CANCELLED"}:
            return (False, f"Failed to write file: {filepath}")
    except IOError as error:
        return (False, f"Failed to write file.\n{str(error)}")
    return (True, f"Saved file: {filepath}")
