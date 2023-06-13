# <pep8 compliant>

from pathlib import Path
from typing import Union

import bpy


def render_image(filepath: Union[Path, str], **keywords):
    """Render image to file.

    :param filepath: Path to PNG file destination.
    :type filepath: Union[Path, str]
    """
    filepath = keywords.pop("filepath", filepath)
    bpy.context.scene.render.filepath = str(filepath)
    bpy.ops.render.render(write_still=True)
