"""
Application entry point.

Usage:
    uv run dspng                # launch the GUI
    uv run dspng file.psd       # open a specific file on startup
    uv run python -m dspng      # alternative invocation
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication


def _import_local():
    """Import MainWindow and DocumentStore, handling both package and script contexts."""
    try:
        from .ui.main_window import MainWindow
        from .psd_manager import DocumentStore
    except ImportError:
        from dspng.ui.main_window import MainWindow
        from dspng.psd_manager import DocumentStore
    return MainWindow, DocumentStore


def main() -> int:
    MainWindow, DocumentStore = _import_local()

    app = QApplication(sys.argv)

    # Basic application metadata (used by Qt for settings paths, etc.)
    app.setApplicationName("dspng")
    app.setOrganizationName("dspng")
    app.setApplicationVersion("1.2.0")

    window = MainWindow()
    window.show()

    # If a PSD path was passed on the command line, open it immediately.
    args = app.arguments()
    if len(args) > 1:
        psd_path = Path(args[1])
        if psd_path.suffix.lower() == ".psd" and psd_path.is_file():
            window._store.add_document(psd_path)
            window._file_list.refresh()
            doc = window._store.selected_document
            window._canvas.set_document(doc)
            window._layer_panel.set_document(doc)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
