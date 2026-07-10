package com.dwine.module.impl.hud;

import com.dwine.Dwine;
import com.dwine.gui.Theme;
import com.dwine.module.HudModule;
import net.minecraft.client.gui.DrawContext;

/** The Dwine wordmark — a small signature in the corner. */
public class WatermarkHud extends HudModule {
    public WatermarkHud() {
        super("Watermark", "Show the Dwine wordmark.", 4, 4);
        setEnabledQuiet(true);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        String label = Dwine.NAME;
        int w = mc.textRenderer.getWidth(label);
        panel(ctx, w, fontHeight());
        text(ctx, label, 0, 0, Theme.accent);
    }
}
