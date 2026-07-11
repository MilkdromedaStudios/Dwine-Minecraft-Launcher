package com.dwine.gui;

/**
 * Central colour palette for the Dwine UI. Flat, modern and translucent —
 * a dark glass panel with a single configurable accent. The launcher's theme
 * choice can push a different accent here through the shared config.
 */
public final class Theme {
    private Theme() {
    }

    public static int accent = 0xFF4F8CFF;      // Dwine blue
    public static int accentSoft = 0x804F8CFF;

    public static final int PANEL = 0xE0121722;   // near-black glass
    public static final int PANEL_LIGHT = 0xE01B2130;
    public static final int HEADER = 0xF00E1420;
    public static final int HOVER = 0x304F8CFF;
    public static final int TEXT = 0xFFF2F5FA;
    public static final int TEXT_DIM = 0xFF8A93A6;
    public static final int TEXT_OFF = 0xFF5A6273;
    public static final int OUTLINE = 0x40FFFFFF;
    public static final int HUD_BG = 0x90121722;

    // Sleek menu / button palette
    public static final int SCRIM = 0xB4090C12;      // full-screen dim behind menus
    public static final int CARD = 0xF21A2130;       // module tile
    public static final int CARD_HOVER = 0xF2222C40;
    public static final int CARD_LINE = 0x22FFFFFF;
    public static final int BTN = 0xF01B2231;        // sleek vanilla-button replacement
    public static final int BTN_HOVER = 0xF02A3855;
    public static final int BTN_OFF = 0xC0161B26;

    /** Blend two ARGB colours; {@code t} = 0 returns a, 1 returns b. */
    public static int mix(int a, int b, float t) {
        t = Math.max(0f, Math.min(1f, t));
        int aa = (a >>> 24) & 0xFF, ar = (a >> 16) & 0xFF, ag = (a >> 8) & 0xFF, ab = a & 0xFF;
        int ba = (b >>> 24) & 0xFF, br = (b >> 16) & 0xFF, bg = (b >> 8) & 0xFF, bb = b & 0xFF;
        int na = (int) (aa + (ba - aa) * t);
        int nr = (int) (ar + (br - ar) * t);
        int ng = (int) (ag + (bg - ag) * t);
        int nb = (int) (ab + (bb - ab) * t);
        return (na << 24) | (nr << 16) | (ng << 8) | nb;
    }

    public static int withAlpha(int color, int alpha) {
        return (color & 0x00FFFFFF) | ((alpha & 0xFF) << 24);
    }
}
