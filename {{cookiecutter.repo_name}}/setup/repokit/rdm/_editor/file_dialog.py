from __future__ import annotations

import os
from pathlib import Path


def browse_for_directory(
    start_path: str | Path | None = None,
    title: str = "Select a folder",
    dir_only: bool = True,
) -> str | None:
    """
    Open a native chooser dialog using wxPython.

    Args:
        start_path: Initial folder or file path to start from.
        title:      Dialog title.
        dir_only:   If True → choose a directory.
                    If False → choose a single file.

    Returns:
        Selected path as a string (directory or file, depending on dir_only),
        or None if cancelled.
    """
    # Local import so non-GUI environments can still import the module
    import wx  # type: ignore

    if start_path:
        start_str = os.fspath(start_path)
    else:
        start_str = os.getcwd()

    app = wx.App(False)

    if dir_only:
        default_dir = start_str
        if os.path.isfile(default_dir):
            default_dir = os.path.dirname(default_dir)

        dlg = wx.DirDialog(
            None,
            message=title,
            defaultPath=default_dir,
            style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON,
        )
    else:
        if os.path.isfile(start_str):
            default_dir, default_file = os.path.split(start_str)
        else:
            default_dir, default_file = (start_str, "")

        dlg = wx.FileDialog(
            None,
            message=title,
            defaultDir=default_dir,
            defaultFile=default_file,
            wildcard="*.*",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )

    try:
        if dlg.ShowModal() == wx.ID_OK:
            selected_path = dlg.GetPath()
        else:
            selected_path = None
    finally:
        dlg.Destroy()
        app.Destroy()

    return selected_path
