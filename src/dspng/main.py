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


def main() -> int:
    # Late import so the module is importable without a display for testing.
    from .ui.main_window import MainWindow

    app = QApplication(sys.argv)

    # Basic application metadata (used by Qt for settings paths, etc.)
    app.setApplicationName("dspng")
    app.setOrganizationName("dspng")
    app.setApplicationVersion("0.1.0")

    window = MainWindow()
    window.show()

    # If a PSD path was passed on the command line, open it immediately.
    args = app.arguments()
    if len(args) > 1:
        psd_path = Path(args[1])
        if psd_path.suffix.lower() == ".psd" and psd_path.is_file():
            from .psd_manager import DocumentStore  # noqa: already created inside window

            # The store lives inside the window; trigger the open flow.
            window._store.add_document(psd_path)
            window._file_list.refresh()
            doc = window._store.selected_document
            window._canvas.set_document(doc)
            window._layer_panel.set_document(doc)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
