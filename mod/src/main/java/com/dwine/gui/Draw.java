package com.dwine.gui;

import net.minecraft.client.gui.DrawContext;

/** Small drawing helpers for the sleek Dwine UI (rounded panels, pills, etc.). */
public final class Draw {
    private Draw() {
    }

    public static void rect(DrawContext ctx, int x, int y, int w, int h, int color) {
        ctx.fill(x, y, x + w, y + h, color);
    }

    /** Filled rounded rectangle (radius is small; corners are quarter-discs). */
    public static void roundedRect(DrawContext ctx, int x, int y, int w, int h, int r, int color) {
        r = Math.max(0, Math.min(r, Math.min(w, h) / 2));
        if (r == 0) {
            ctx.fill(x, y, x + w, y + h, color);
            return;
        }
        ctx.fill(x + r, y, x + w - r, y + h, color);      // centre column
        ctx.fill(x, y + r, x + r, y + h - r, color);      // left band
        ctx.fill(x + w - r, y + r, x + w, y + h - r, color); // right band
        corner(ctx, x + r, y + r, r, color, true, true);
        corner(ctx, x + w - r, y + r, r, color, false, true);
        corner(ctx, x + r, y + h - r, r, color, true, false);
        corner(ctx, x + w - r, y + h - r, r, color, false, false);
    }

    /** 1px rounded outline. */
    public static void roundedOutline(DrawContext ctx, int x, int y, int w, int h, int r, int color) {
        r = Math.max(0, Math.min(r, Math.min(w, h) / 2));
        ctx.fill(x + r, y, x + w - r, y + 1, color);          // top
        ctx.fill(x + r, y + h - 1, x + w - r, y + h, color);  // bottom
        ctx.fill(x, y + r, x + 1, y + h - r, color);          // left
        ctx.fill(x + w - 1, y + r, x + w, y + h - r, color);  // right
        ring(ctx, x + r, y + r, r, color, true, true);
        ring(ctx, x + w - r, y + r, r, color, false, true);
        ring(ctx, x + r, y + h - r, r, color, true, false);
        ring(ctx, x + w - r, y + h - r, r, color, false, false);
    }

    /** A horizontal on/off pill switch (iOS-style). */
    public static void toggle(DrawContext ctx, int x, int y, int w, int h, boolean on, int accent) {
        int track = on ? Theme.withAlpha(accent, 0xFF) : 0xFF3A4152;
        roundedRect(ctx, x, y, w, h, h / 2, track);
        int knob = h - 4;
        int kx = on ? x + w - knob - 2 : x + 2;
        roundedRect(ctx, kx, y + 2, knob, knob, knob / 2, 0xFFF2F5FA);
    }

    private static void corner(DrawContext ctx, int cx, int cy, int r, int color,
                               boolean left, boolean top) {
        for (int dy = 0; dy < r; dy++) {
            for (int dx = 0; dx < r; dx++) {
                if (dx * dx + dy * dy <= r * r) {
                    int px = left ? cx - 1 - dx : cx + dx;
                    int py = top ? cy - 1 - dy : cy + dy;
                    ctx.fill(px, py, px + 1, py + 1, color);
                }
            }
        }
    }

    private static void ring(DrawContext ctx, int cx, int cy, int r, int color,
                             boolean left, boolean top) {
        for (int dy = 0; dy < r; dy++) {
            for (int dx = 0; dx < r; dx++) {
                int d2 = dx * dx + dy * dy;
                if (d2 <= r * r && d2 >= (r - 1) * (r - 1)) {
                    int px = left ? cx - 1 - dx : cx + dx;
                    int py = top ? cy - 1 - dy : cy + dy;
                    ctx.fill(px, py, px + 1, py + 1, color);
                }
            }
        }
    }
}
