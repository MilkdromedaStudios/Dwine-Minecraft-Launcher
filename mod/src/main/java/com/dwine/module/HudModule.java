package com.dwine.module;

import com.dwine.gui.Theme;
import com.dwine.setting.BooleanSetting;
import com.dwine.setting.NumberSetting;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.util.math.MatrixStack;

/**
 * A module that draws something onto the in-game HUD. Position is stored in
 * screen pixels (top-left anchored) and is editable by dragging in the HUD
 * editor. Subclasses draw relative to the local origin (0, 0); this class
 * handles translation and scaling.
 */
public abstract class HudModule extends Module {
    private int x;
    private int y;
    private int width = 40;
    private int height = 12;

    protected final NumberSetting scale;
    protected final BooleanSetting background;
    protected final BooleanSetting shadow;

    protected HudModule(String name, String description, int defaultX, int defaultY) {
        super(name, description, Category.HUD);
        this.x = defaultX;
        this.y = defaultY;
        this.scale = add(new NumberSetting("Scale", "Element scale", 1.0, 0.5, 2.0, 0.05));
        this.background = add(new BooleanSetting("Background", "Draw a panel behind the element", true));
        this.shadow = add(new BooleanSetting("Text shadow", "Draw text with a drop shadow", true));
    }

    /** Draw the element. Called from the HUD render callback while enabled. */
    public final void render(DrawContext ctx) {
        float s = scale.getFloat();
        MatrixStack matrices = ctx.getMatrices();
        matrices.push();
        matrices.translate(x, y, 0);
        matrices.scale(s, s, 1f);
        renderHud(ctx);
        matrices.pop();
    }

    /** Subclasses draw here in local coordinates (origin at the element's top-left). */
    protected abstract void renderHud(DrawContext ctx);

    // -- drawing helpers ------------------------------------------------

    /** Draw a background panel behind the element (local coords). */
    protected void panel(DrawContext ctx, int w, int h) {
        setSize(w, h);
        if (background.get()) {
            ctx.fill(-2, -2, w + 2, h + 2, Theme.HUD_BG);
            ctx.fill(-2, -2, w + 2, -1, Theme.accentSoft);
        }
    }

    /** Draw a line of text (local coords) using the theme colours. */
    protected int text(DrawContext ctx, String value, int lx, int ly, int color) {
        ctx.drawText(mc.textRenderer, value, lx, ly, color, shadow.get());
        return mc.textRenderer.getWidth(value);
    }

    protected int text(DrawContext ctx, String value, int lx, int ly) {
        return text(ctx, value, lx, ly, Theme.TEXT);
    }

    protected int fontHeight() {
        return mc.textRenderer.fontHeight;
    }

    protected void setSize(int w, int h) {
        this.width = Math.max(1, w);
        this.height = Math.max(1, h);
    }

    // -- geometry (screen space, for the editor) ------------------------

    public int getX() {
        return x;
    }

    public int getY() {
        return y;
    }

    public int getScaledWidth() {
        return Math.round((width + 4) * scale.getFloat());
    }

    public int getScaledHeight() {
        return Math.round((height + 4) * scale.getFloat());
    }

    public void setPosition(int x, int y) {
        this.x = x;
        this.y = y;
    }

    /** Nudge the element scale (used by scroll in the HUD editor). */
    public void addScale(double delta) {
        scale.set(scale.get() + delta);
    }

    /** Keep the element on-screen after a resize. */
    public void clampTo(int screenW, int screenH) {
        x = Math.max(0, Math.min(screenW - getScaledWidth(), x));
        y = Math.max(0, Math.min(screenH - getScaledHeight(), y));
    }
}
