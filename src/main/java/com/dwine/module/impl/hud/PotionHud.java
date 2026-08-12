package com.dwine.module.impl.hud;

import com.dwine.gui.Theme;
import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.world.effect.MobEffectInstance;

import java.util.ArrayList;
import java.util.List;

/** Active status effects with remaining time. */
public class PotionHud extends HudModule {
    public PotionHud() {
        super("Potions", "Show active status effects.", 4, 172);
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        if (mc.player == null) {
            return;
        }
        List<String> lines = new ArrayList<>();
        for (MobEffectInstance effect : mc.player.getActiveEffects()) {
            lines.add(describe(effect));
        }
        if (lines.isEmpty()) {
            setSize(mc.font.width("No effects"), fontHeight());
            return;
        }
        int width = 0;
        for (String line : lines) {
            width = Math.max(width, mc.font.width(line));
        }
        int lineHeight = fontHeight() + 1;
        panel(ctx, width, lines.size() * lineHeight - 1);
        int y = 0;
        for (String line : lines) {
            text(ctx, line, 0, y, Theme.TEXT);
            y += lineHeight;
        }
    }

    private String describe(MobEffectInstance effect) {
        String name = effect.getEffect().value().getDisplayName().getString();
        int amplifier = effect.getAmplifier();
        if (amplifier > 0) {
            name += " " + (amplifier + 1);
        }
        String time = effect.isInfiniteDuration() ? "∞" : format(effect.getDuration());
        return name + " " + time;
    }

    private static String format(int ticks) {
        int seconds = ticks / 20;
        return String.format("%d:%02d", seconds / 60, seconds % 60);
    }
}
