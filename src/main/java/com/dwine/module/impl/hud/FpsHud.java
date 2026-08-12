package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;

/** Current framerate. */
public class FpsHud extends HudModule {
    public FpsHud() {
        super("FPS", "Show the current framerate.", 4, 18);
        setEnabledQuiet(true);
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        String label = mc.getFps() + " FPS";
        panel(ctx, mc.font.width(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
