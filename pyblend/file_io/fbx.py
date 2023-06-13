"""This module provides file operations for FBX files."""
# <pep8 compliant>

from pathlib import Path

import bpy
from io_scene_fbx import export_fbx_bin  # noqa Usually comes with Blender.
from pyblend.operators import DummyOperator


def export_fbx(filepath: Path | str, **kwargs) -> tuple[bool, str]:
    """Export FBX file.

    It's a wrapper for the FBX add-on's save function. It accepts the export settings as keyword arguments.

    :param filepath: Path to FBX file destination.
    :param kwargs: Export settings.
    :return: A tuple with it's first element indicating whether export was successful, a message as the second element.
    """
    # The exporter add-on's function expects a string.
    filepath = str(filepath)
    # Check if the file has a valid extension.
    if not filepath.lower().endswith(".fbx"):
        return (False, f"Destination file is not an FBX file: {filepath}")
    # Create a pseudo operator needed for export function.
    pseudo_operator = DummyOperator()
    try:
        if export_fbx_bin.save(pseudo_operator, bpy.context, filepath=filepath, **kwargs) == {"CANCELLED"}:
            return (False, f"Failed to write file: {filepath}")
    except IOError as error:
        return (False, f"Failed to write file: {filepath}\n{str(error)}")
    return (True, f"Saved file: {filepath}")
