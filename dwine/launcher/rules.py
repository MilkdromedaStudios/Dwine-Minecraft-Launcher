"""Evaluation of Mojang's library/argument rule objects.

Version JSON files gate libraries and arguments on OS, architecture and
launcher feature flags. This module answers "does this rule list allow
the current platform?" exactly like the vanilla launcher does.
"""

from __future__ import annotations

import platform
import sys
from typing import Any


def current_os() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "osx"
    return "linux"


def current_arch() -> str:
    machine = platform.machine().lower()
    if machine in ("amd64", "x86_64"):
        return "x64"
    if machine in ("aarch64", "arm64"):
        return "arm64"
    if machine in ("i386", "i686", "x86"):
        return "x86"
    return machine


def _match_os(os_rule: dict[str, Any]) -> bool:
    if "name" in os_rule and os_rule["name"] != current_os():
        return False
    if "arch" in os_rule and os_rule["arch"] not in (current_arch(), platform.machine().lower()):
        return False
    if "version" in os_rule:
        import re

        if not re.search(os_rule["version"], platform.version() or ""):
            return False
    return True


def rules_allow(
    rules: list[dict[str, Any]] | None,
    features: dict[str, bool] | None = None,
) -> bool:
    """Return True if the rule list permits inclusion on this platform."""
    if not rules:
        return True
    features = features or {}
    allowed = False
    for rule in rules:
        applies = True
        if "os" in rule:
            applies = applies and _match_os(rule["os"])
        if "features" in rule:
            for key, wanted in rule["features"].items():
                applies = applies and (features.get(key, False) == wanted)
        if applies:
            allowed = rule.get("action") == "allow"
    return allowed


def substitute(template: str, variables: dict[str, str]) -> str:
    """Replace ``${key}`` placeholders, leaving unknown keys empty."""
    out = template
    for key, value in variables.items():
        out = out.replace("${" + key + "}", value)
    # Any leftover placeholder becomes empty rather than leaking literally.
    import re

    return re.sub(r"\$\{[^}]+\}", "", out)
