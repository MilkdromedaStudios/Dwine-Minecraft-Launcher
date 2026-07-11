package com.dwine.gui;

import com.dwine.Dwine;
import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import org.lwjgl.glfw.GLFW;

/**
 * Drag-and-drop editor for HUD elements. Every enabled HUD element renders
 * exactly where it will appear in-game, wrapped in a grab box; drag to move,
 * scroll to scale.
 */
public class HudEditorScreen extends Screen {
    private HudModule dragging;
    private int dragOffX;
    private int dragOffY;

    public HudEditorScreen() {
        super(Component.literal("Dwine HUD Editor"));
    }

    @Override
    public void render(GuiGraphics ctx, int mouseX, int mouseY, float delta) {
        this.renderBackground(ctx, mouseX, mouseY, delta);
        ctx.drawString(font, "HUD Editor", 16, 8, Theme.accent, false);
        ctx.drawString(font, "drag to move  ·  scroll to resize  ·  esc to close", 78, 9, Theme.TEXT_DIM, false);

        for (HudModule hud : Dwine.modules.getHudModules()) {
            if (!hud.isEnabled()) {
                continue;
            }
            hud.render(ctx);
            int x = hud.getX();
            int y = hud.getY();
            int w = Math.max(8, hud.getScaledWidth());
            int h = Math.max(8, hud.getScaledHeight());
            boolean hover = mouseX >= x && mouseX <= x + w && mouseY >= y && mouseY <= y + h;
            ctx.fill(x - 1, y - 1, x + w + 1, y + h + 1, hover ? Theme.HOVER : 0x20FFFFFF);
            ctx.renderOutline(x - 1, y - 1, w + 2, h + 2, hover ? Theme.accent : Theme.OUTLINE);
        }
        super.render(ctx, mouseX, mouseY, delta);
    }

    @Override
    public boolean mouseClicked(double mouseX, double mouseY, int button) {
        HudModule hit = pick(mouseX, mouseY);
        if (hit != null) {
            dragging = hit;
            dragOffX = (int) mouseX - hit.getX();
            dragOffY = (int) mouseY - hit.getY();
            return true;
        }
        return super.mouseClicked(mouseX, mouseY, button);
    }

    @Override
    public boolean mouseDragged(double mouseX, double mouseY, int button, double dx, double dy) {
        if (dragging != null) {
            int nx = (int) mouseX - dragOffX;
            int ny = (int) mouseY - dragOffY;
            dragging.setPosition(nx, ny);
            dragging.clampTo(this.width, this.height);
            return true;
        }
        return super.mouseDragged(mouseX, mouseY, button, dx, dy);
    }

    @Override
    public boolean mouseReleased(double mouseX, double mouseY, int button) {
        dragging = null;
        return super.mouseReleased(mouseX, mouseY, button);
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double horizontalAmount, double verticalAmount) {
        HudModule hit = pick(mouseX, mouseY);
        if (hit != null) {
            hit.addScale(verticalAmount * 0.1);
            return true;
        }
        return super.mouseScrolled(mouseX, mouseY, horizontalAmount, verticalAmount);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (keyCode == Dwine.config.hudEditorKey) {
            onClose();
            return true;
        }
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    @Override
    public void onClose() {
        if (Dwine.config != null) {
            Dwine.config.save();
        }
        super.onClose();
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    private HudModule pick(double mouseX, double mouseY) {
        HudModule found = null;
        for (HudModule hud : Dwine.modules.getHudModules()) {
            if (!hud.isEnabled()) {
                continue;
            }
            int x = hud.getX();
            int y = hud.getY();
            int w = Math.max(8, hud.getScaledWidth());
            int h = Math.max(8, hud.getScaledHeight());
            if (mouseX >= x && mouseX <= x + w && mouseY >= y && mouseY <= y + h) {
                found = hud; // last match wins → topmost drawn
            }
        }
        return found;
    }
}
