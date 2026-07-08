"""Dwine's built-in feature system.

Features are cosmetic or quality-of-life only. Each one is implemented
by one of four mechanisms:

* ``mod``      — a vetted, open Modrinth mod installed per version
* ``theme``    — Dwine's generated in-game resource pack
* ``launcher`` — the Python launcher itself (RPC, screenshots, ...)
* ``companion``— configuration for the Dwine companion mod

The safety policy (:mod:`dwine.features.safety`) is applied to every
launch and cannot be disabled per-feature: restricted features are
forced off on multiplayer, and radar-like tools are swapped for their
fair-play variants on competitive networks.
"""
