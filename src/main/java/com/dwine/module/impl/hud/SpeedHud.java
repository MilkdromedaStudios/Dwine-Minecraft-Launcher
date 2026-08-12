package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;

/** Horizontal movement speed in blocks per second. */
public class SpeedHud extends HudModule {
    private double lastX;
    private double lastZ;
    private double speed;

    public SpeedHud() {
        super("Speed", "Show your horizontal speed.", 4, 102);
    }

    @Override
    public void onTick() {
        if (mc.player == null) {
            return;
        }
        double dx = mc.player.getX() - lastX;
        double dz = mc.player.getZ() - lastZ;
        speed = Math.sqrt(dx * dx + dz * dz) * 20.0;
        lastX = mc.player.getX();
        lastZ = mc.player.getZ();
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        String label = String.format("%.2f b/s", speed);
        panel(ctx, mc.font.width(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
