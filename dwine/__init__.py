"""Dwine — a lean, fully legitimate Minecraft launcher for modded play.

Dwine does four things and does them well:

* Installs and launches every Minecraft version (Vanilla, Fabric, Quilt, Forge).
* Manages client mods, resource packs and shaders from Modrinth's official API.
* Signs you in with a Microsoft link code — no Azure setup required.
* Wraps it in a small PySide6 launcher UI with a Play button.

No cheats. No packet manipulation. No unfair advantage. Ever.
"""

__version__ = "0.1.0"
__app_name__ = "Dwine"
__author__ = "Milkdromeda Studios"
__url__ = "https://github.com/MilkdromedaStudios/Dwine"

USER_AGENT = f"MilkdromedaStudios/Dwine/{__version__} (github.com/MilkdromedaStudios/Dwine)"
