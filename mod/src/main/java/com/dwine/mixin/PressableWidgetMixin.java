package com.dwine.mixin;

import com.dwine.gui.Draw;
import com.dwine.gui.Theme;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.AbstractButton;
import net.minecraft.client.gui.components.AbstractWidget;
import net.minecraft.network.chat.Component;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.injection.At;
import org.spongepowered.asm.mixin.injection.Inject;
import org.spongepowered.asm.mixin.injection.callback.CallbackInfo;

/**
 * Replaces the flat vanilla button texture with a sleek, rounded, accented
 * button — applied to every standard pressable button (title screen, pause
 * menu, options, …). Icon-only buttons (empty label) are left untouched so
 * their glyphs still show.
 */
@Mixin(AbstractButton.class)
public class PressableWidgetMixin {

    @Inject(method = "renderWidget", at = @At("HEAD"), cancellable = true)
    private void dwine$sleekButton(GuiGraphics ctx, int mouseX, int mouseY, float delta, CallbackInfo ci) {
        AbstractWidget self = (AbstractWidget) (Object) this;
        Component message = self.getMessage();
        if (message == null || message.getString().isEmpty()) {
            return; // icon button — let vanilla draw it
        }
        int x = self.getX();
        int y = self.getY();
        int w = self.getWidth();
        int h = self.getHeight();
        if (w <= 0 || h <= 0) {
            return;
        }
        Minecraft mc = Minecraft.getInstance();
        // Skip icon buttons (label wider than the button, e.g. the language /
        // accessibility globes) so their glyphs still render via vanilla.
        if (w < 30 || mc.font.width(message) > w - 6) {
            return;
        }
        boolean active = self.active;
        boolean hovered = active && mouseX >= x && mouseX < x + w && mouseY >= y && mouseY < y + h;

        int radius = Math.min(6, h / 2);
        int base = !active ? Theme.BTN_OFF : (hovered ? Theme.BTN_HOVER : Theme.BTN);
        Draw.roundedRect(ctx, x, y, w, h, radius, base);
        Draw.rect(ctx, x + radius, y + 1, w - 2 * radius, 1, 0x14FFFFFF);
        Draw.roundedOutline(ctx, x, y, w, h, radius, hovered ? Theme.accent : Theme.CARD_LINE);
        if (hovered) {
            Draw.rect(ctx, x + radius, y + h - 2, w - 2 * radius, 1, Theme.accentSoft);
        }

        int textColor = active ? Theme.TEXT : Theme.TEXT_OFF;
        int tw = mc.font.width(message);
        ctx.drawString(mc.font, message, x + (w - tw) / 2, y + (h - mc.font.lineHeight) / 2 + 1, textColor, false);
        ci.cancel();
    }
}
