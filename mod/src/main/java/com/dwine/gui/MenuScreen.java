package com.dwine.gui;

import com.dwine.Dwine;
import com.dwine.module.Category;
import com.dwine.module.Module;
import com.dwine.setting.BooleanSetting;
import com.dwine.setting.ModeSetting;
import com.dwine.setting.NumberSetting;
import com.dwine.setting.Setting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.List;

/**
 * The Dwine menu — a clean, modern tile picker. Categories along the top, a
 * grid of module cards with iOS-style toggles, and a settings sheet per module.
 * Deliberately styled like a polished client's settings screen, not a ClickGUI.
 */
public class MenuScreen extends Screen {
    private static final int PAD = 16;
    private static final int COLS = 3;
    private static final int CARD_H = 44;
    private static final int GAP = 8;

    private Category category = Category.HUD;
    private int scroll;
    private Module sheetModule;         // module whose settings sheet is open
    private Module bindingModule;       // module awaiting a key bind
    private NumberSetting draggingSlider;
    private int sliderX;
    private int sliderW;

    public MenuScreen() {
        super(Component.literal("Dwine"));
    }

    // -- geometry ------------------------------------------------------

    private int[] panel() {
        int pw = Math.min(width - 40, 470);
        int ph = Math.min(height - 40, 264);
        return new int[]{(width - pw) / 2, (height - ph) / 2, pw, ph};
    }

    private int[] tabRect(int index, int[] p) {
        int tabW = (p[2] - PAD * 2 - GAP * (Category.values().length - 1)) / Category.values().length;
        int x = p[0] + PAD + index * (tabW + GAP);
        return new int[]{x, p[1] + 30, tabW, 18};
    }

    private int gridTop(int[] p) {
        return p[1] + 56;
    }

    private int gridBottom(int[] p) {
        return p[1] + p[3] - 22;
    }

    private List<Object[]> cards(int[] p) {
        List<Object[]> out = new ArrayList<>();
        int gridLeft = p[0] + PAD;
        int usable = p[2] - PAD * 2;
        int colW = (usable - GAP * (COLS - 1)) / COLS;
        List<Module> mods = Dwine.modules.getByCategory(category);
        int top = gridTop(p);
        for (int i = 0; i < mods.size(); i++) {
            int col = i % COLS;
            int row = i / COLS;
            int cx = gridLeft + col * (colW + GAP);
            int cy = top + row * (CARD_H + GAP) - scroll;
            out.add(new Object[]{mods.get(i), cx, cy, colW, CARD_H});
        }
        return out;
    }

    private int maxScroll(int[] p) {
        int rows = (Dwine.modules.getByCategory(category).size() + COLS - 1) / COLS;
        int contentH = rows * (CARD_H + GAP) - GAP;
        int viewH = gridBottom(p) - gridTop(p);
        return Math.max(0, contentH - viewH);
    }

    // -- rendering -----------------------------------------------------

    @Override
    public void render(GuiGraphics ctx, int mouseX, int mouseY, float delta) {
        ctx.fill(0, 0, width, height, Theme.SCRIM);
        int[] p = panel();
        Draw.roundedRect(ctx, p[0], p[1], p[2], p[3], 8, Theme.PANEL);
        Draw.roundedOutline(ctx, p[0], p[1], p[2], p[3], 8, Theme.CARD_LINE);

        ctx.drawString(font, "Dwine", p[0] + PAD, p[1] + 13, Theme.accent, false);
        int nameW = font.width("Dwine");
        ctx.drawString(font, "client " + Dwine.VERSION, p[0] + PAD + nameW + 6, p[1] + 13, Theme.TEXT_DIM, false);
        String hint = "Esc to close   ·   HUD editor: hold Right Ctrl";
        ctx.drawString(font, hint, p[0] + p[2] - PAD - font.width(hint), p[1] + 13, Theme.TEXT_OFF, false);

        // tabs
        Category[] cats = Category.values();
        for (int i = 0; i < cats.length; i++) {
            int[] t = tabRect(i, p);
            boolean sel = cats[i] == category;
            boolean hov = inside(mouseX, mouseY, t);
            Draw.roundedRect(ctx, t[0], t[1], t[2], t[3], 6, sel ? Theme.accent : (hov ? Theme.CARD_HOVER : Theme.CARD));
            String title = cats[i].getTitle();
            int tw = font.width(title);
            ctx.drawString(font, title, t[0] + (t[2] - tw) / 2, t[1] + 5,
                    sel ? 0xFF0E1420 : Theme.TEXT, false);
        }

        // card grid (clipped)
        int gl = p[0] + PAD - 2, gt = gridTop(p), gr = p[0] + p[2] - PAD + 2, gb = gridBottom(p);
        ctx.enableScissor(gl, gt, gr, gb);
        for (Object[] c : cards(p)) {
            renderCard(ctx, (Module) c[0], (int) c[1], (int) c[2], (int) c[3], (int) c[4], mouseX, mouseY);
        }
        ctx.disableScissor();

        // scrollbar
        int ms = maxScroll(p);
        if (ms > 0) {
            int trackH = gb - gt;
            int barH = Math.max(16, trackH * trackH / (trackH + ms));
            int barY = gt + (trackH - barH) * scroll / ms;
            Draw.roundedRect(ctx, gr, gt, 2, trackH, 1, Theme.CARD_LINE);
            Draw.roundedRect(ctx, gr, barY, 2, barH, 1, Theme.accentSoft);
        }

        if (sheetModule != null) {
            renderSheet(ctx, p, mouseX, mouseY);
        }
        super.render(ctx, mouseX, mouseY, delta);
    }

    private void renderCard(GuiGraphics ctx, Module m, int x, int y, int w, int h, int mouseX, int mouseY) {
        boolean hov = inside(mouseX, mouseY, new int[]{x, y, w, h}) && sheetModule == null;
        Draw.roundedRect(ctx, x, y, w, h, 6, hov ? Theme.CARD_HOVER : Theme.CARD);
        if (m.isEnabled()) {
            Draw.roundedRect(ctx, x, y + 8, 2, h - 16, 1, Theme.accent); // accent rail
        }
        String name = font.plainSubstrByWidth(m.getName(), w - 16);
        ctx.drawString(font, name, x + 8, y + 7, m.isEnabled() ? Theme.TEXT : Theme.TEXT_DIM, false);
        String desc = font.plainSubstrByWidth(m.getDescription(), w - 40);
        ctx.drawString(font, desc, x + 8, y + 19, Theme.TEXT_OFF, false);
        // toggle pill
        Draw.toggle(ctx, x + 8, y + h - 15, 18, 10, m.isEnabled(), Theme.accent);
        // gear (settings) affordance if the module has settings
        if (!m.getSettings().isEmpty()) {
            int gx = x + w - 16, gy = y + h - 15;
            boolean gh = inside(mouseX, mouseY, new int[]{gx - 2, gy - 2, 14, 14});
            ctx.drawString(font, "⚙", gx, gy, gh ? Theme.accent : Theme.TEXT_DIM, false);
        }
    }

    private void renderSheet(GuiGraphics ctx, int[] p, int mouseX, int mouseY) {
        ctx.fill(p[0], p[1], p[0] + p[2], p[1] + p[3], 0xCC0B0E15);
        List<Setting> settings = sheetModule.getSettings();
        int rows = settings.size();
        int sw = Math.min(300, p[2] - 40);
        int sh = 52 + rows * 22 + 26;
        int sx = p[0] + (p[2] - sw) / 2;
        int sy = p[1] + (p[3] - sh) / 2;
        Draw.roundedRect(ctx, sx, sy, sw, sh, 8, Theme.PANEL_LIGHT);
        Draw.roundedOutline(ctx, sx, sy, sw, sh, 8, Theme.accentSoft);

        ctx.drawString(font, sheetModule.getName(), sx + 14, sy + 12, Theme.TEXT, false);
        boolean closeHover = inside(mouseX, mouseY, new int[]{sx + sw - 20, sy + 10, 12, 12});
        ctx.drawString(font, "✕", sx + sw - 18, sy + 11, closeHover ? Theme.accent : Theme.TEXT_DIM, false);

        int y = sy + 34;
        // bind row
        String keyLabel = bindingModule == sheetModule ? "press a key…" : "Key: " + keyName(sheetModule.getKeyCode());
        ctx.drawString(font, keyLabel, sx + 14, y, bindingModule == sheetModule ? Theme.accent : Theme.TEXT_DIM, false);
        y += 18;

        for (Setting s : settings) {
            renderSetting(ctx, s, sx + 14, y, sw - 28, mouseX);
            y += 22;
        }
    }

    private void renderSetting(GuiGraphics ctx, Setting s, int x, int y, int w, int mouseX) {
        if (s instanceof BooleanSetting b) {
            ctx.drawString(font, s.getName(), x, y + 1, Theme.TEXT_DIM, false);
            Draw.toggle(ctx, x + w - 20, y - 1, 18, 10, b.get(), Theme.accent);
        } else if (s instanceof NumberSetting n) {
            ctx.drawString(font, s.getName() + ": " + fmt(n.get()), x, y - 3, Theme.TEXT_DIM, false);
            int tx = x, tw = w, ty = y + 9;
            Draw.roundedRect(ctx, tx, ty, tw, 3, 1, Theme.CARD);
            int fill = (int) Math.round(tw * n.getFraction());
            Draw.roundedRect(ctx, tx, ty, Math.max(2, fill), 3, 1, Theme.accent);
            Draw.roundedRect(ctx, tx + fill - 2, ty - 2, 4, 7, 2, Theme.TEXT);
        } else if (s instanceof ModeSetting m) {
            ctx.drawString(font, s.getName(), x, y + 1, Theme.TEXT_DIM, false);
            String v = m.get();
            ctx.drawString(font, v, x + w - font.width(v), y + 1, Theme.accent, false);
        }
    }

    // -- input ---------------------------------------------------------

    @Override
    public boolean mouseClicked(double mouseX, double mouseY, int button) {
        int[] p = panel();
        if (sheetModule != null) {
            return sheetClicked(mouseX, mouseY, button, p);
        }
        // tabs
        Category[] cats = Category.values();
        for (int i = 0; i < cats.length; i++) {
            if (inside((int) mouseX, (int) mouseY, tabRect(i, p))) {
                category = cats[i];
                scroll = 0;
                return true;
            }
        }
        // cards
        if (mouseY >= gridTop(p) && mouseY <= gridBottom(p)) {
            for (Object[] c : cards(p)) {
                int x = (int) c[1], y = (int) c[2], w = (int) c[3], h = (int) c[4];
                if (!inside((int) mouseX, (int) mouseY, new int[]{x, y, w, h})) {
                    continue;
                }
                Module m = (Module) c[0];
                boolean onGear = !m.getSettings().isEmpty() && mouseX >= x + w - 18 && mouseY >= y + h - 17;
                if (onGear) {
                    sheetModule = m;
                } else {
                    m.toggle();
                }
                return true;
            }
        }
        return super.mouseClicked(mouseX, mouseY, button);
    }

    private boolean sheetClicked(double mouseX, double mouseY, int button, int[] p) {
        List<Setting> settings = sheetModule.getSettings();
        int sw = Math.min(300, p[2] - 40);
        int sh = 52 + settings.size() * 22 + 26;
        int sx = p[0] + (p[2] - sw) / 2;
        int sy = p[1] + (p[3] - sh) / 2;
        if (mouseX < sx || mouseX > sx + sw || mouseY < sy || mouseY > sy + sh) {
            sheetModule = null;
            bindingModule = null;
            return true;
        }
        if (mouseX >= sx + sw - 22 && mouseY <= sy + 22) {
            sheetModule = null;
            bindingModule = null;
            return true;
        }
        // bind row
        int y = sy + 34;
        if (mouseY >= y - 2 && mouseY < y + 14) {
            bindingModule = bindingModule == sheetModule ? null : sheetModule;
            return true;
        }
        y += 18;
        for (Setting s : settings) {
            if (mouseY >= y - 4 && mouseY < y + 16) {
                handleSetting(s, mouseX, sx + 14, sw - 28, button);
                return true;
            }
            y += 22;
        }
        return true;
    }

    private void handleSetting(Setting s, double mouseX, int x, int w, int button) {
        if (s instanceof BooleanSetting b) {
            b.toggle();
        } else if (s instanceof NumberSetting n) {
            draggingSlider = n;
            sliderX = x;
            sliderW = w;
            n.setFraction((mouseX - x) / w);
        } else if (s instanceof ModeSetting m) {
            if (button == 1) {
                m.cycleBack();
            } else {
                m.cycle();
            }
        }
    }

    @Override
    public boolean mouseDragged(double mouseX, double mouseY, int button, double dx, double dy) {
        if (draggingSlider != null) {
            draggingSlider.setFraction((mouseX - sliderX) / sliderW);
            return true;
        }
        return super.mouseDragged(mouseX, mouseY, button, dx, dy);
    }

    @Override
    public boolean mouseReleased(double mouseX, double mouseY, int button) {
        draggingSlider = null;
        return super.mouseReleased(mouseX, mouseY, button);
    }

    @Override
    public boolean mouseScrolled(double mouseX, double mouseY, double h, double v) {
        if (sheetModule == null) {
            scroll = clamp(scroll - (int) (v * 18), 0, maxScroll(panel()));
            return true;
        }
        return super.mouseScrolled(mouseX, mouseY, h, v);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (bindingModule != null) {
            bindingModule.setKeyCode(keyCode == GLFW.GLFW_KEY_ESCAPE ? GLFW.GLFW_KEY_UNKNOWN : keyCode);
            bindingModule = null;
            return true;
        }
        if (sheetModule != null && keyCode == GLFW.GLFW_KEY_ESCAPE) {
            sheetModule = null;
            return true;
        }
        if (keyCode == Dwine.config.clickGuiKey) {
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

    // -- helpers -------------------------------------------------------

    private static boolean inside(int mx, int my, int[] r) {
        return mx >= r[0] && mx <= r[0] + r[2] && my >= r[1] && my <= r[1] + r[3];
    }

    private static int clamp(int v, int lo, int hi) {
        return Math.max(lo, Math.min(hi, v));
    }

    private static String fmt(double v) {
        return v == Math.rint(v) ? String.format("%.0f", v) : String.format("%.2f", v);
    }

    private static String keyName(int key) {
        if (key == GLFW.GLFW_KEY_UNKNOWN) {
            return "none";
        }
        String n = GLFW.glfwGetKeyName(key, 0);
        return n != null ? n.toUpperCase() : "KEY " + key;
    }
}
