package com.dwine;

import java.util.Map;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Native 26.2 Dwine module menu. */
public final class DwineScreen extends Screen {
    public DwineScreen(Component title) {
        super(title);
    }

    @Override
    protected void init() {
        int startX = this.width / 2 - 230;
        int startY = 92;
        int index = 0;

        for (Map.Entry<String, Boolean> entry : DwineFeatures.INSTANCE.all().entrySet()) {
            String name = entry.getKey();
            int col = index % 2;
            int row = index / 2;
            Button button = Button.builder(label(name), b -> {
                        boolean enabled = DwineFeatures.INSTANCE.toggle(name);
                        b.setMessage(Component.literal(name + (enabled ? "  • ON" : "  • OFF")));
                    })
                    .bounds(startX + col * 240, startY + row * 30, 220, 24)
                    .build();
            this.addRenderableWidget(button);
            index++;
        }

        this.addRenderableWidget(Button.builder(Component.literal("Done"), b -> this.minecraft.gui.setScreen(null))
                .bounds(this.width / 2 - 110, startY + 5 * 30 + 14, 220, 24)
                .build());
    }

    private Component label(String name) {
        return Component.literal(name + (DwineFeatures.INSTANCE.enabled(name) ? "  • ON" : "  • OFF"));
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float delta) {
        super.extractRenderState(graphics, mouseX, mouseY, delta);
        graphics.text(this.font, "DWINE", this.width / 2 - 230, 30, 0xFF9C8CFF, true);
        graphics.text(this.font, "Minecraft 26.2 client modules", this.width / 2 - 230, 47, 0xFFFFFFFF, true);
        graphics.text(this.font, "Right Shift: menu   •   C: zoom (when enabled)", this.width / 2 - 230, 64, 0xFF9AA8C1, true);
        graphics.text(this.font, "Settings save automatically to config/dwine/features-26.2.properties", this.width / 2 - 230, 78, 0xFF78869E, true);
    }
}
