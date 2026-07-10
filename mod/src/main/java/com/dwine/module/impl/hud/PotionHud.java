package com.dwine.module.impl.hud;

import com.dwine.gui.Theme;
import com.dwine.module.HudModule;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.entity.effect.StatusEffectInstance;

import java.util.ArrayList;
import java.util.List;

/** Active status effects with remaining time. */
public class PotionHud extends HudModule {
    public PotionHud() {
        super("Potions", "Show active status effects.", 4, 172);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        if (mc.player == null) {
            return;
        }
        List<String> lines = new ArrayList<>();
        for (StatusEffectInstance effect : mc.player.getStatusEffects()) {
            lines.add(describe(effect));
        }
        if (lines.isEmpty()) {
            setSize(mc.textRenderer.getWidth("No effects"), fontHeight());
            return;
        }
        int width = 0;
        for (String line : lines) {
            width = Math.max(width, mc.textRenderer.getWidth(line));
        }
        int lineHeight = fontHeight() + 1;
        panel(ctx, width, lines.size() * lineHeight - 1);
        int y = 0;
        for (String line : lines) {
            text(ctx, line, 0, y, Theme.TEXT);
            y += lineHeight;
        }
    }

    private String describe(StatusEffectInstance effect) {
        String name = effect.getEffectType().value().getName().getString();
        int amplifier = effect.getAmplifier();
        if (amplifier > 0) {
            name += " " + (amplifier + 1);
        }
        String time = effect.isInfinite() ? "∞" : format(effect.getDuration());
        return name + " " + time;
    }

    private static String format(int ticks) {
        int seconds = ticks / 20;
        return String.format("%d:%02d", seconds / 60, seconds % 60);
    }
}
