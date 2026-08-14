package com.dwine;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.network.chat.Component;

/** Dwine-styled button: dark glass card, violet accent rail, hover highlight and compact text. */
public final class DwineButton extends Button {
    private final boolean compact;

    public DwineButton(int x, int y, int width, int height, Component message, OnPress onPress) {
        this(x, y, width, height, message, onPress, false);
    }

    public DwineButton(int x, int y, int width, int height, Component message, OnPress onPress, boolean compact) {
        super(x, y, width, height, message, onPress, DEFAULT_NARRATION);
        this.compact = compact;
    }

    @Override
    protected void extractContents(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float delta) {
        boolean hover = isHovered();
        int x = getX();
        int y = getY();
        int bg = hover ? 0xFF2B3153 : 0xFF20253E;
        int line = this.active ? (hover ? 0xFFB7A9FF : 0xFF8E7CFF) : 0xFF50566F;
        // Paint over the vanilla button body so every Dwine-owned control has its own skin.
        graphics.fill(x, y, x + this.width, y + this.height, bg);
        graphics.fill(x, y, x + 3, y + this.height, line);
        if (hover) graphics.fill(x + 3, y, x + this.width, y + 1, 0x557C8BFF);
        int textY = y + (this.height - 8) / 2;
        int color = this.active ? 0xFFF2F4FF : 0xFF7F879E;
        graphics.centeredText(MinecraftHolder.font(), getMessage(), x + this.width / 2 + (compact ? 1 : 0), textY, color);
    }

    private static final class MinecraftHolder {
        static net.minecraft.client.gui.Font font() {
            return net.minecraft.client.Minecraft.getInstance().font;
        }
    }
}
