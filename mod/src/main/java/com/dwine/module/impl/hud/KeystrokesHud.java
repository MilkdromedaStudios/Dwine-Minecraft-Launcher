package com.dwine.module.impl.hud;

import com.dwine.gui.Theme;
import com.dwine.module.HudModule;
import net.minecraft.client.gui.DrawContext;

/** WASD + mouse + space keystroke display. */
public class KeystrokesHud extends HudModule {
    private static final int BOX = 16;
    private static final int GAP = 1;
    private static final int STEP = BOX + GAP;

    public KeystrokesHud() {
        super("Keystrokes", "Show WASD, mouse and jump keys.", 4, 130);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        if (mc.options == null) {
            return;
        }
        int wide = 3 * BOX + 2 * GAP; // 50
        setSize(wide, 3 * STEP + 7);

        key(ctx, STEP, 0, BOX, BOX, "W", mc.options.forwardKey.isPressed());
        key(ctx, 0, STEP, BOX, BOX, "A", mc.options.leftKey.isPressed());
        key(ctx, STEP, STEP, BOX, BOX, "S", mc.options.backKey.isPressed());
        key(ctx, 2 * STEP, STEP, BOX, BOX, "D", mc.options.rightKey.isPressed());

        int half = (wide - GAP) / 2;
        key(ctx, 0, 2 * STEP, half, BOX, "LMB", mc.options.attackKey.isPressed());
        key(ctx, half + GAP, 2 * STEP, wide - half - GAP, BOX, "RMB", mc.options.useKey.isPressed());

        key(ctx, 0, 3 * STEP, wide, 6, "", mc.options.jumpKey.isPressed());
    }

    private void key(DrawContext ctx, int x, int y, int w, int h, String label, boolean pressed) {
        int bg = pressed ? Theme.accent : Theme.HUD_BG;
        int fg = pressed ? 0xFF0E1420 : Theme.TEXT;
        ctx.fill(x, y, x + w, y + h, bg);
        if (!label.isEmpty()) {
            int tw = mc.textRenderer.getWidth(label);
            ctx.drawText(mc.textRenderer, label, x + (w - tw) / 2, y + (h - fontHeight()) / 2 + 1, fg, shadow.get());
        }
    }
}
