package com.dwine;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** HUD configuration surface modeled after the original Dwine HUD editor. */
public final class DwineHudScreen extends Screen {
    private static final String[] HUD = {"Watermark", "FPS", "Coordinates", "Keystrokes"};

    public DwineHudScreen(Component title) {
        super(title);
    }

    @Override
    protected void init() {
        int x = this.width / 2 - 180;
        int y = 92;
        for (int i = 0; i < HUD.length; i++) {
            String name = HUD[i];
            this.addRenderableWidget(Button.builder(label(name), b -> {
                        boolean enabled = DwineFeatures.INSTANCE.toggle(name);
                        b.setMessage(Component.literal(name + (enabled ? "   VISIBLE" : "   HIDDEN")));
                    })
                    .bounds(x, y + i * 32, 360, 24)
                    .build());
        }

        this.addRenderableWidget(Button.builder(Component.literal("Back to Modules"), b ->
                        this.minecraft.gui.setScreen(new DwineScreen(Component.literal("Dwine"))))
                .bounds(x, y + 4 * 32 + 20, 360, 24)
                .build());
    }

    private Component label(String name) {
        return Component.literal(name + (DwineFeatures.INSTANCE.enabled(name) ? "   VISIBLE" : "   HIDDEN"));
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float delta) {
        super.extractRenderState(graphics, mouseX, mouseY, delta);
        int x = this.width / 2 - 205;
        graphics.fill(0, 0, 10000, 10000, 0xE9080B16);
        graphics.fill(x, 26, x + 410, 280, 0xF5161A2C);
        graphics.fill(x, 26, x + 410, 80, 0xFF202647);
        graphics.fill(x, 79, x + 410, 81, 0xFF8E7CFF);
        graphics.text(this.font, "DWINE HUD EDITOR", x + 20, 43, 0xFFB8A7FF, true);
        graphics.text(this.font, "Choose which widgets appear in game", x + 20, 61, 0xFF9CA7C4, false);
        graphics.text(this.font, "Live HUD preview is visible behind this screen when in a world.", x + 20, 246, 0xFF7783A6, false);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
