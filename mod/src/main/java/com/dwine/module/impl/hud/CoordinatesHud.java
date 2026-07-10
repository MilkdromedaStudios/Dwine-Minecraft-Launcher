package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.util.math.BlockPos;

/** Player block coordinates. */
public class CoordinatesHud extends HudModule {
    public CoordinatesHud() {
        super("Coordinates", "Show your XYZ position.", 4, 30);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        if (mc.player == null) {
            return;
        }
        BlockPos p = mc.player.getBlockPos();
        String label = "XYZ " + p.getX() + " " + p.getY() + " " + p.getZ();
        panel(ctx, mc.textRenderer.getWidth(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
