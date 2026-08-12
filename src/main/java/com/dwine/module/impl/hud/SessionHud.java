package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;

/** Time elapsed since the game launched. */
public class SessionHud extends HudModule {
    private final long start = System.currentTimeMillis();

    public SessionHud() {
        super("Session", "Show how long this session has run.", 4, 78);
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        long seconds = (System.currentTimeMillis() - start) / 1000L;
        String label = "Session " + String.format("%02d:%02d:%02d",
                seconds / 3600, (seconds % 3600) / 60, seconds % 60);
        panel(ctx, mc.font.width(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
