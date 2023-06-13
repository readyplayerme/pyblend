import bpy


def create_library_override(datablock):
    """Create library overrides on a linked data-block.

    :param datablock: Data-block for which to create library overrides.
    """
    if hasattr(datablock, "override_library") and not datablock.override_library:
        datablock.override_create(remap_local_usages=True)


def make_override_editable(datablock):
    """Make an data-block's library override editable."""
    # Skip if no library override.
    if not datablock.override_library:
        return
    # It's already editable, skip.
    if not datablock.override_library.is_system_override:
        return

    ctx = bpy.context.copy()
    ctx["id"] = datablock.override_library.id_data
    with bpy.context.temp_override(**ctx):
        bpy.ops.ed.lib_id_override_editable_toggle()
