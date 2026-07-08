"""Crash analyzer: turns crash reports and logs into human advice."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# (name, regex, advice) — first match of each pattern is reported once.
_PATTERNS: list[tuple[str, str, str]] = [
    (
        "Out of memory",
        r"java\.lang\.OutOfMemoryError",
        "The game ran out of RAM. Raise memory in Settings → Game → Memory "
        "(4–6 GB is plenty for modded; more can make it worse).",
    ),
    (
        "Missing Fabric dependency",
        r"requires [^\n]*? of (?:mod )?'?(?P<mod>[\w.-]+?)'?, which is missing",
        "A mod is missing a dependency ('{mod}'). Open Mods and install it, "
        "or use one-click install which resolves dependencies automatically.",
    ),
    (
        "Fabric loader dependency error",
        r"net\.fabricmc\.loader\.impl\.FormattedException",
        "Fabric refused to start because of a mod dependency/version problem. "
        "The lines just below this error name the mod — update or remove it.",
    ),
    (
        "Forge missing dependencies",
        r"Missing or unsupported mandatory dependencies",
        "Forge reports missing mandatory dependencies. Check the mod list in "
        "the report and install the named dependencies for your exact version.",
    ),
    (
        "Mod built for another Minecraft version",
        r"(?:Incompatible mods found|intermediary mappings|Mod resolution failed)",
        "At least one mod was built for a different Minecraft version. Use "
        "Mods → Update All, which re-resolves every mod against this profile's version.",
    ),
    (
        "Mixin conflict",
        r"(?:MixinApplyError|Mixin apply failed|CRITICAL.*mixin)",
        "Two mods patch the same code (mixin conflict). The report names the "
        "mixin owner — try removing/updating that mod first.",
    ),
    (
        "Broken graphics driver / GL error",
        r"(?:GLFW error|Failed to create.*GL|1282: Invalid operation|WGL: The driver)",
        "OpenGL/driver failure. Update your GPU driver; if you use shaders, "
        "try disabling them; on laptops force the dedicated GPU for Java.",
    ),
    (
        "Wrong Java version",
        r"(?:UnsupportedClassVersionError|class file version (?P<ver>[\d.]+))",
        "The installed Java is too old for this Minecraft version. Dwine can "
        "manage Java for you — clear Settings → Game → Java path to use it.",
    ),
    (
        "Corrupted world / chunk",
        r"(?:Exception ticking world|Chunk file at [^\n]* is in the wrong location)",
        "A world/chunk failed to load. Restore the world from backup, or use "
        "region tools to remove the corrupted chunk noted in the report.",
    ),
    (
        "Sodium + incompatible rendering mod",
        r"(?:sodium[^\n]*(?:incompatible|conflict)|RenderDoc)",
        "A rendering mod conflicts with Sodium. Iris replaces OptiFine-style "
        "shaders; OptiFine itself is not compatible with Sodium profiles.",
    ),
    (
        "Server connection issue",
        r"(?:Connection timed out|Connection refused|Failed to connect to the server)",
        "Network problem, not a crash: check the address in the server list, "
        "your firewall, and use Tools → Ping Tester to measure reachability.",
    ),
]


@dataclass
class Finding:
    title: str
    advice: str
    evidence: str


def analyze_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for title, pattern, advice in _PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        rendered = advice
        for key, value in (match.groupdict() or {}).items():
            if value:
                rendered = rendered.replace("{" + key + "}", value)
        start = max(0, match.start() - 120)
        evidence = text[start : match.end() + 120].strip()
        findings.append(Finding(title=title, advice=rendered, evidence=evidence))
    return findings


def analyze_file(path: Path) -> list[Finding]:
    return analyze_text(Path(path).read_text(encoding="utf-8", errors="replace"))


def latest_crash_report(game_dir: Path) -> Path | None:
    reports = sorted(
        (game_dir / "crash-reports").glob("crash-*.txt"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return reports[0] if reports else None
