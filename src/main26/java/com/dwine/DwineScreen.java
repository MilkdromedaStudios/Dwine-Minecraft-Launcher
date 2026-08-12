package com.dwine;

import java.util.Map;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Branded Dwine 26.2 module menu inspired by the original client UI. */
public final class DwineScreen extends Screen {
    public DwineScreen(Component title) {
        super(title);
    }

    @Override
    protected void init() {
        int panelX = this.width / 2 - 245;
        int startY = 102;
        int index = 0;

        for (Map.Entry<String, Boolean> entry : DwineFeatures.INSTANCE.all().entrySet()) {
            String name = entry.getKey();
            int col = index % 2;
            int row = index / 2;
            Button button = Button.builder(label(name), b -> {
                        boolean enabled = DwineFeatures.INSTANCE.toggle(name);
                        b.setMessage(Component.literal(name + (enabled ? "   ON" : "   OFF")));
                    })
                    .bounds(panelX + 18 + col * 230, startY + row * 31, 214, 24)
                    .build();
            this.addRenderableWidget(button);
            index++;
        }

        this.addRenderableWidget(Button.builder(Component.literal("HUD Editor"), b ->
                        this.minecraft.gui.setScreen(new DwineHudScreen(Component.literal("Dwine HUD"))))
                .bounds(panelX + 18, startY + 5 * 31 + 15, 214, 24)
                .build());

        this.addRenderableWidget(Button.builder(Component.literal("Done"), b -> this.minecraft.gui.setScreen(null))
                .bounds(panelX + 248, startY + 5 * 31 + 15, 214, 24)
                .build());
    }

    private Component label(String name) {
        return Component.literal(name + (DwineFeatures.INSTANCE.enabled(name) ? "   ON" : "   OFF"));
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float delta) {
        super.extractRenderState(graphics, mouseX, mouseY, delta);
        int x = this.width / 2 - 245;
        int y = 22;
        graphics.fill(0, 0, 10000, 10000, 0xD9080B16);
        graphics.fill(x, y, x + 490, y + 286, 0xF5161A2C);
        graphics.fill(x, y, x + 490, y + 54, 0xFF202647);
        graphics.fill(x, y + 53, x + 490, y + 55, 0xFF8E7CFF);
        graphics.text(this.font, "DWINE", x + 18, y + 15, 0xFFB8A7FF, true);
        graphics.text(this.font, "client 0.5 • Minecraft 26.2", x + 74, y + 15, 0xFFA8B0C8, false);
        graphics.text(this.font, "Modules", x + 18, y + 68, 0xFFFFFFFF, true);
        graphics.text(this.font, "HUD / Render / Movement", x + 74, y + 68, 0xFF7783A6, false);
        graphics.text(this.font, "RShift or J closes/opens Dwine • C zoom", x + 18, y + 266, 0xFF7783A6, false);
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
