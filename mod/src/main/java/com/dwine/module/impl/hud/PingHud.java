package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.network.PlayerListEntry;

/** Latency to the current server. */
public class PingHud extends HudModule {
    public PingHud() {
        super("Ping", "Show your latency to the server.", 4, 54);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        String label = "-- ms";
        if (mc.getNetworkHandler() != null && mc.player != null) {
            PlayerListEntry entry = mc.getNetworkHandler().getPlayerListEntry(mc.player.getUuid());
            if (entry != null) {
                label = entry.getLatency() + " ms";
            }
        }
        panel(ctx, mc.textRenderer.getWidth(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
