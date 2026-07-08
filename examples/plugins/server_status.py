"""Example Dwine plugin: pings your favourite server when the launcher starts.

Copy this file into your Dwine plugins directory
(``~/.local/share/dwine/plugins`` on Linux, ``%APPDATA%/Dwine/plugins`` on
Windows) and it will load automatically. List plugins with
``dwine plugins``.
"""

PLUGIN = {
    "id": "server-status",
    "name": "Server Status",
    "version": "1.0",
}

FAVOURITE = "mc.hypixel.net"


def setup(api):
    def check(*_args):
        from dwine.tools.ping import ping

        try:
            result = ping(api.get_setting("host", FAVOURITE))
            api.emit("status", {
                "online": result.players_online,
                "latency": result.latency_ms,
            })
        except OSError:
            pass

    api.register_command("check", check)
    api.on("theme.changed", check)  # cheap "launcher is alive" hook
