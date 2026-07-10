package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.DrawContext;

/** Current framerate. */
public class FpsHud extends HudModule {
    public FpsHud() {
        super("FPS", "Show the current framerate.", 4, 18);
        setEnabledQuiet(true);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        String label = mc.getCurrentFps() + " FPS";
        panel(ctx, mc.textRenderer.getWidth(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
