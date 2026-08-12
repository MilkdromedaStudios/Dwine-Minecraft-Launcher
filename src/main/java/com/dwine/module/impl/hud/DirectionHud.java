package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.core.Direction;

/** Cardinal facing plus the axis you are looking along. */
public class DirectionHud extends HudModule {
    public DirectionHud() {
        super("Direction", "Show the direction you are facing.", 4, 42);
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        if (mc.player == null) {
            return;
        }
        Direction dir = mc.player.getDirection();
        String label = "Facing: " + cardinal(dir) + " (" + axis(dir) + ")";
        panel(ctx, mc.font.width(label), fontHeight());
        text(ctx, label, 0, 0);
    }

    private static String cardinal(Direction dir) {
        return switch (dir) {
            case NORTH -> "North";
            case SOUTH -> "South";
            case EAST -> "East";
            case WEST -> "West";
            default -> dir.getName();
        };
    }

    private static String axis(Direction dir) {
        return switch (dir) {
            case NORTH -> "-Z";
            case SOUTH -> "+Z";
            case EAST -> "+X";
            case WEST -> "-X";
            default -> "?";
        };
    }
}
