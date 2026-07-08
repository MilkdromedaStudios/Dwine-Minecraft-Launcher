"""The Dwine safety policy — non-negotiable, applied to every launch.

Dwine's promise is "never bannable", and this module is where that
promise is enforced in code rather than in marketing copy:

1. Input-automation features are forced OFF for any multiplayer target.
   They only ever run in singleplayer, regardless of user settings.
2. Radar-like tools (cave maps, entity radar) are swapped for their
   fair-play variants when joining a known competitive network.
3. Nothing in Dwine touches packets, movement, combat, or server-visible
   behavior. The catalog in :mod:`dwine.features.registry` is reviewed
   against this rule; this module double-checks flags at launch time.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..core.events import bus
from .registry import FEATURES, FLAG_INPUT_AUTOMATION, FLAG_RADAR_LIKE

# Networks with strict modification policies. Matching is by hostname
# suffix, so play.hypixel.net, mc.hypixel.net etc. are all covered.
COMPETITIVE_NETWORKS: tuple[str, ...] = (
    "hypixel.net",
    "hypixel.io",
    "cubecraft.net",
    "minemen.club",
    "pvp.land",
    "hoplite.gg",
    "vanillaclub.net",
    "purplemc.net",
    "wynncraft.com",
    "mccisland.net",
)


@dataclass
class Enforcement:
    feature_id: str
    action: str  # "disabled" | "fair_play_variant"
    reason: str


def normalize_host(address: str) -> str:
    host = address.strip().lower()
    if "://" in host:
        host = host.split("://", 1)[1]
    host = host.split("/", 1)[0]
    host = host.rsplit(":", 1)[0] if host.count(":") == 1 else host
    return host


def is_competitive(address: str) -> bool:
    host = normalize_host(address)
    return any(
        host == network or host.endswith("." + network)
        for network in COMPETITIVE_NETWORKS
    )


def enforce(enabled: dict[str, bool], server: str | None) -> list[Enforcement]:
    """Adjust the effective feature map in place for this launch target.

    ``server`` is None for singleplayer / main-menu launches. Multiplayer
    is treated conservatively: automation is off for *any* server, not
    just known competitive ones, because Dwine cannot know every
    network's rules.
    """
    actions: list[Enforcement] = []
    multiplayer = server is not None
    competitive = bool(server) and is_competitive(server)

    for fid, feature in FEATURES.items():
        if not enabled.get(fid):
            continue
        if FLAG_INPUT_AUTOMATION in feature.flags and multiplayer:
            enabled[fid] = False
            actions.append(
                Enforcement(
                    fid,
                    "disabled",
                    "input automation never runs on multiplayer servers",
                )
            )
        elif FLAG_RADAR_LIKE in feature.flags and competitive:
            if feature.competitive_alternative:
                actions.append(
                    Enforcement(
                        fid,
                        "fair_play_variant",
                        f"competitive network detected — using "
                        f"{feature.competitive_alternative}",
                    )
                )
            else:
                enabled[fid] = False
                actions.append(
                    Enforcement(
                        fid,
                        "disabled",
                        "radar-like feature has no fair-play variant",
                    )
                )

    for action in actions:
        bus.emit(
            "safety.enforced",
            {"feature": action.feature_id, "action": action.action, "reason": action.reason},
        )
    return actions


def audit_catalog() -> list[str]:
    """Sanity checks on the catalog itself. Returns a list of violations.

    Run by the test suite: an empty list is a hard requirement for any
    Dwine release.
    """
    problems: list[str] = []
    banned_words = ("killaura", "aimbot", "reach", "velocity", "autototem", "scaffold")
    for fid, feature in FEATURES.items():
        text = (feature.name + " " + feature.description).lower()
        for word in banned_words:
            if word in text:
                problems.append(f"{fid}: mentions '{word}'")
        if FLAG_INPUT_AUTOMATION in feature.flags and feature.default_enabled:
            problems.append(f"{fid}: automation features must default to OFF")
        if FLAG_INPUT_AUTOMATION in feature.flags and not feature.options.get(
            "singleplayer_only", True
        ):
            problems.append(f"{fid}: automation features must be singleplayer-only")
    return problems
