"""General purpose functions that are not specific to certain data-blocks."""
import logging
import math
from pathlib import Path

import bpy


def cleanup_unused_data():
    """Remove unused data blocks."""
    blocks_types = [
        bpy.data.meshes,
        bpy.data.materials,
        bpy.data.textures,
        bpy.data.images,
        bpy.data.armatures,
        bpy.data.objects,
        bpy.data.collections,
    ]
    for blocks in blocks_types:
        for block in blocks:
            if not block.users and hasattr(blocks, "remove"):
                blocks.remove(block)
    unused_libs = [lib for lib in bpy.data.libraries if not lib.users_id]
    bpy.data.batch_remove(unused_libs)


def import_node_group(
    source_path: Path | str,
    name: str,
    link: bool = True,
    relative: bool = True,
) -> bpy.types.NodeGroup | None:
    """Import a node group from a different file."""
    try:
        with bpy.data.libraries.load(filepath=str(source_path), link=link, relative=relative) as (_, data_to):
            data_to.node_groups = [name]
    except IOError:
        logging.error(f"Could not import node group '{name}' from '{source_path}'.")
        return None
    # If the node group was not found, data_to.node_groups[0] will be None.
    return data_to.node_groups[0]


def srgb_to_linear(srgb_value: float) -> float:
    """Convert from sRGB to Linear RGB.

    Based on https://en.wikipedia.org/wiki/SRGB#From_sRGB_to_CIE_XYZ
    """
    return srgb_value / 12.92 if srgb_value <= 0.04045 else math.pow((srgb_value + 0.055) / 1.055, 2.4)


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert a hex color string to linear RGB."""
    hex_color = hex_color.lstrip("#")
    # Convert hex to decimal values.
    rgb = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    # Normalize values.
    return tuple(srgb_to_linear(x / 255.0) for x in rgb)
