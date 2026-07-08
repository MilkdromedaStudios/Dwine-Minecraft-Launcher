"""Auto-cleaner: reclaims disk from logs, crash reports and stale caches.

Only files that are always safe to delete are touched: rotated game
logs, old crash reports, and Dwine's own download cache. Worlds,
configs, screenshots and mods are never candidates.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from ..core import paths
from ..core.config import get_config
from ..launcher.profiles import Profile


@dataclass
class CleanReport:
    files: list[Path] = field(default_factory=list)
    bytes_freed: int = 0

    def merge(self, other: "CleanReport") -> None:
        self.files.extend(other.files)
        self.bytes_freed += other.bytes_freed


def _sweep(
    candidates: list[Path], max_age_days: float, dry_run: bool
) -> CleanReport:
    report = CleanReport()
    cutoff = time.time() - max_age_days * 86400
    for file in candidates:
        try:
            if not file.is_file() or file.stat().st_mtime > cutoff:
                continue
            size = file.stat().st_size
            if not dry_run:
                file.unlink()
            report.files.append(file)
            report.bytes_freed += size
        except OSError:
            continue
    return report


def clean_profile(profile: Profile, dry_run: bool = True) -> CleanReport:
    cfg = get_config()
    max_age = float(cfg.get("performance.auto_clean.max_log_age_days", 14))
    report = CleanReport()
    game = profile.game_dir
    report.merge(_sweep(list((game / "logs").glob("*.log.gz")), max_age, dry_run))
    report.merge(_sweep(list((game / "logs").glob("*.log")), max_age, dry_run))
    report.merge(
        _sweep(list((game / "crash-reports").glob("crash-*.txt")), max_age, dry_run)
    )
    report.merge(_sweep(list((game / ".mixin.out").rglob("*")), max_age, dry_run))
    return report


def clean_cache(dry_run: bool = True) -> CleanReport:
    """Trim Dwine's download cache to the configured budget (oldest first)."""
    cfg = get_config()
    budget = int(cfg.get("performance.auto_clean.max_cache_mb", 2048)) * 1024 * 1024
    cache = paths.cache_dir()
    if not cache.exists():
        return CleanReport()
    files = sorted(
        (f for f in cache.rglob("*") if f.is_file()),
        key=lambda f: f.stat().st_mtime,
    )
    total = sum(f.stat().st_size for f in files)
    report = CleanReport()
    for file in files:
        if total <= budget:
            break
        size = file.stat().st_size
        if not dry_run:
            try:
                file.unlink()
            except OSError:
                continue
        total -= size
        report.files.append(file)
        report.bytes_freed += size
    return report


def clean_all(profiles: list[Profile], dry_run: bool = True) -> CleanReport:
    report = clean_cache(dry_run=dry_run)
    for profile in profiles:
        report.merge(clean_profile(profile, dry_run=dry_run))
    return report


def human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"
