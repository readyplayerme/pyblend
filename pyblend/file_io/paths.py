"""Convenience functions for working with file-system paths in Blender."""
# <pep8 compliant>
import re
from pathlib import Path

import addon_utils
import bpy


def path_exists(path: Path) -> bool:
    """Check if a path exists and is a directory.

    :param path: Path to check.
    :return: True if path exists and is a directory.
    """
    return path.exists() and path.is_dir()


def paths_exist(paths: list[Path]) -> bool:
    """Check if all paths exist and are directories.

    :param paths: Paths to check.
    :return: True if all paths exist and are directories.
    """
    return all(path_exists(path) for path in paths)


def get_abs_path(path: str | Path) -> Path:
    """Get absolute path. Handles Blender's special path '//'.

    :param path: Relative path or Blender's special path ('//').
    :type path: Union[str, Path]
    :return: Absolute path.
    :rtype: Path
    """
    if isinstance(path, Path):
        return path.resolve()
    return Path(bpy.path.abspath(path)).resolve()


def filename_as(filepath: str, ext: str) -> str:
    """Get name of file with another file extension.

    :parem filepath: Path to file with old filename.
    :type filepath: str
    :param ext: New file extension.
    :type ext: str
    :return: New file name.
    :rtype: str
    """
    blend_name = bpy.path.basename(filepath)
    if not blend_name:
        return ""
    new_name = Path(blend_name).with_suffix(f'.{ext.strip(".").lower()}')
    return str(new_name)


def remove_shape_suffix(filepath: Path | str) -> Path:
    """Remove shape suffix from file name, e.g. -m or -f in a file name.

    :param filepath: Path to file with shape suffix.
    :return: Path to new file name without shape suffix.
    """
    filepath = Path(filepath)
    new_name = re.sub(r"(.*)-\w$", r"\g<1>", filepath.stem)
    return filepath.with_stem(new_name)


def get_addon_path(addon_name: str) -> Path | None:
    """Return the path to the add-on folder."""
    return next((Path(mod.__file__).parent for mod in addon_utils.modules() if mod.bl_info["name"] == addon_name), None)


def get_addon_name(addon_path: str | Path) -> Path | None:
    """Return the name of the add-on given a path."""
    addon_path = get_abs_path(addon_path)
    addon_names = (
        mod.bl_info["name"] for mod in addon_utils.modules() if Path(mod.__file__).parent in addon_path.parents
    )
    return next(addon_names, None)
