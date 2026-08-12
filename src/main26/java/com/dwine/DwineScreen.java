package com.dwine;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Simple native 26.2 control screen opened by Dwine's configurable key mapping. */
public final class DwineScreen extends Screen {
    public DwineScreen(Component title) {
        super(title);
    }

    @Override
    protected void init() {
        int x = this.width / 2 - 110;
        int y = this.height / 2 - 10;

        this.addRenderableWidget(Button.builder(
                Component.literal("Dwine 26.2 • Active"),
                button -> { })
                .bounds(x, y, 220, 20)
                .build());

        this.addRenderableWidget(Button.builder(
                Component.literal("Close"),
                button -> Minecraft.getInstance().setScreen(null))
                .bounds(x, y + 34, 220, 20)
                .build());
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float delta) {
        super.extractRenderState(graphics, mouseX, mouseY, delta);
        graphics.text(this.font, "Dwine Client", 28, 28, 0xFFFFFFFF, true);
        graphics.text(this.font, "Minecraft 26.2 / Fabric", 28, 44, 0xFF9AA8C1, true);
        graphics.text(this.font, "Managed locally by the Dwine companion launcher", 28, 60, 0xFF9AA8C1, true);
    }
}
