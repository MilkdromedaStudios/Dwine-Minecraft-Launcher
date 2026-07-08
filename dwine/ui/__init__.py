"""The Dwine launcher UI (PySide6).

The UI is an optional extra: ``pip install dwine[ui]``. Everything the
launcher does is also available headless through ``dwine --help``.
"""


def run() -> int:
    """Start the launcher UI. Raises a helpful error if PySide6 is missing."""
    try:
        from .app import main
    except ImportError as exc:  # pragma: no cover
        raise SystemExit(
            "The Dwine UI needs PySide6. Install it with:\n"
            "    pip install dwine[ui]\n"
            f"(import error: {exc})"
        ) from exc
    return main()
