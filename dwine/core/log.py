"""Logging setup: rotating launcher log + console output."""

from __future__ import annotations

import logging
import logging.handlers
import sys

from . import paths

_FORMAT = "%(asctime)s %(levelname)-7s %(name)s: %(message)s"


def setup(verbose: bool = False) -> logging.Logger:
    root = logging.getLogger("dwine")
    if root.handlers:
        return root
    root.setLevel(logging.DEBUG)

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.DEBUG if verbose else logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)-7s %(message)s"))
    root.addHandler(console)

    try:
        paths.logs_dir().mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            paths.logs_dir() / "launcher.log",
            maxBytes=2 << 20,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(file_handler)
    except OSError:
        pass
    return root


def get(name: str) -> logging.Logger:
    return logging.getLogger(f"dwine.{name}")
