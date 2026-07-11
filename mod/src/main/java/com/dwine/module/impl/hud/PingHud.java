package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.multiplayer.PlayerInfo;

/** Latency to the current server. */
public class PingHud extends HudModule {
    public PingHud() {
        super("Ping", "Show your latency to the server.", 4, 54);
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        String label = "-- ms";
        if (mc.getConnection() != null && mc.player != null) {
            PlayerInfo entry = mc.getConnection().getPlayerInfo(mc.player.getUUID());
            if (entry != null) {
                label = entry.getLatency() + " ms";
            }
        }
        panel(ctx, mc.font.width(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
