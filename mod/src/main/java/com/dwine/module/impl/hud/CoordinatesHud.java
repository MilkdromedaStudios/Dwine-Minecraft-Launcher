package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.core.BlockPos;

/** Player block coordinates. */
public class CoordinatesHud extends HudModule {
    public CoordinatesHud() {
        super("Coordinates", "Show your XYZ position.", 4, 30);
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        if (mc.player == null) {
            return;
        }
        BlockPos p = mc.player.blockPosition();
        String label = "XYZ " + p.getX() + " " + p.getY() + " " + p.getZ();
        panel(ctx, mc.font.width(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
