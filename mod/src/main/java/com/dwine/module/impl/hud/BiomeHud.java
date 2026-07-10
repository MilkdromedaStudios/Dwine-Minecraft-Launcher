package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.DrawContext;

/** Name of the biome you are standing in. */
public class BiomeHud extends HudModule {
    public BiomeHud() {
        super("Biome", "Show your current biome.", 4, 90);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        if (mc.player == null || mc.world == null) {
            return;
        }
        String path = mc.world.getBiome(mc.player.getBlockPos())
                .getKey()
                .map(key -> key.getValue().getPath())
                .orElse("unknown");
        String label = "Biome: " + prettify(path);
        panel(ctx, mc.textRenderer.getWidth(label), fontHeight());
        text(ctx, label, 0, 0);
    }

    private static String prettify(String path) {
        String[] parts = path.replace('_', ' ').split(" ");
        StringBuilder sb = new StringBuilder();
        for (String part : parts) {
            if (part.isEmpty()) {
                continue;
            }
            sb.append(Character.toUpperCase(part.charAt(0))).append(part.substring(1)).append(' ');
        }
        return sb.toString().trim();
    }
}
