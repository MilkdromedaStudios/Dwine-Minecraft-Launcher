package com.dwine.gui;

import com.dwine.Dwine;
import com.dwine.module.Category;
import com.dwine.module.Module;
import com.dwine.setting.BooleanSetting;
import com.dwine.setting.ModeSetting;
import com.dwine.setting.NumberSetting;
import com.dwine.setting.Setting;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.client.gui.screen.Screen;
import net.minecraft.text.Text;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.EnumMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * The Dwine ClickGUI — a flat, translucent, draggable module panel per
 * category. Left-click toggles a module, right-click expands its settings,
 * left-click a module's key badge to rebind it.
 */
public class ClickGuiScreen extends Screen {
    private static final int PANEL_WIDTH = 122;
    private static final int HEADER_HEIGHT = 16;
    private static final int ROW_HEIGHT = 14;

    private final Map<Category, int[]> panelPos = new EnumMap<>(Category.class);
    private final Set<Module> expanded = new HashSet<>();

    private Category draggingPanel;
    private int dragOffX;
    private int dragOffY;

    private NumberSetting draggingSlider;
    private int sliderX;
    private int sliderW;

    private Module bindingModule;

    private enum Kind { HEADER, MODULE, SETTING }

    private static final class Row {
        Kind kind;
        Category category;
        Module module;
        Setting setting;
        int x;
        int y;
        int w;
        int h;
    }

    public ClickGuiScreen() {
        super(Text.literal("Dwine"));
    }

    @Override
    protected void init() {
        int x = 16;
        int y = 24;
        int i = 0;
        for (Category category : Category.values()) {
            if (!panelPos.containsKey(category)) {
                panelPos.put(category, new int[]{x + i * (PANEL_WIDTH + 10), y});
            }
            i++;
        }
    }

    // -- layout --------------------------------------------------------

    private List<Row> layout() {
        List<Row> rows = new ArrayList<>();
        for (Category category : Category.values()) {
            int[] pos = panelPos.get(category);
            int px = pos[0];
            int py = pos[1];
            rows.add(row(Kind.HEADER, category, null, null, px, py, PANEL_WIDTH, HEADER_HEIGHT));
            int cy = py + HEADER_HEIGHT;
            for (Module module : Dwine.modules.getByCategory(category)) {
                rows.add(row(Kind.MODULE, category, module, null, px, cy, PANEL_WIDTH, ROW_HEIGHT));
                cy += ROW_HEIGHT;
                if (expanded.contains(module)) {
                    for (Setting setting : module.getSettings()) {
                        int h = setting instanceof NumberSetting ? 20 : 12;
                        rows.add(row(Kind.SETTING, category, module, setting, px, cy, PANEL_WIDTH, h));
                        cy += h;
                    }
                }
            }
        }
        return rows;
    }

    private Row row(Kind kind, Category cat, Module module, Setting setting, int x, int y, int w, int h) {
        Row r = new Row();
        r.kind = kind;
        r.category = cat;
        r.module = module;
        r.setting = setting;
        r.x = x;
        r.y = y;
        r.w = w;
        r.h = h;
        return r;
    }

    // -- rendering -----------------------------------------------------

    @Override
    public void render(DrawContext ctx, int mouseX, int mouseY, float delta) {
        this.renderBackground(ctx, mouseX, mouseY, delta);

        ctx.drawText(textRenderer, "Dwine", 16, 8, Theme.accent, false);
        ctx.drawText(textRenderer,
                "client " + Dwine.VERSION + "  ·  right-click to expand  ·  drag headers  ·  esc to close",
                58, 9, Theme.TEXT_DIM, false);

        for (Row r : layout()) {
            boolean hovered = contains(r, mouseX, mouseY);
            switch (r.kind) {
                case HEADER -> drawHeader(ctx, r);
                case MODULE -> drawModule(ctx, r, hovered);
                case SETTING -> drawSetting(ctx, r, mouseX);
            }
        }
        super.render(ctx, mouseX, mouseY, delta);
    }

    private void drawHeader(DrawContext ctx, Row r) {
        ctx.fill(r.x, r.y, r.x + r.w, r.y + r.h, Theme.HEADER);
        ctx.fill(r.x, r.y + r.h - 1, r.x + r.w, r.y + r.h, Theme.accent);
        ctx.drawText(textRenderer, r.category.getTitle(), r.x + 7, r.y + 4, Theme.TEXT, false);
    }

    private void drawModule(DrawContext ctx, Row r, boolean hovered) {
        boolean on = r.module.isEnabled();
        int bg = hovered ? Theme.HOVER : (on ? Theme.PANEL_LIGHT : Theme.PANEL);
        ctx.fill(r.x, r.y, r.x + r.w, r.y + r.h, bg);
        if (on) {
            ctx.fill(r.x, r.y, r.x + 2, r.y + r.h, Theme.accent);
        }
        ctx.drawText(textRenderer, r.module.getName(), r.x + 8, r.y + 3, on ? Theme.TEXT : Theme.TEXT_DIM, false);

        String badge = bindingModule == r.module ? "..." : keyName(r.module.getKeyCode());
        int bw = textRenderer.getWidth(badge);
        ctx.drawText(textRenderer, badge, r.x + r.w - bw - 5, r.y + 3,
                bindingModule == r.module ? Theme.accent : Theme.TEXT_OFF, false);
    }

    private void drawSetting(DrawContext ctx, Row r, int mouseX) {
        ctx.fill(r.x, r.y, r.x + r.w, r.y + r.h, Theme.PANEL);
        int indent = r.x + 12;
        Setting s = r.setting;
        if (s instanceof BooleanSetting b) {
            ctx.drawText(textRenderer, s.getName(), indent, r.y + 2, Theme.TEXT_DIM, false);
            int box = 8;
            int bx = r.x + r.w - box - 6;
            int by = r.y + 2;
            ctx.fill(bx, by, bx + box, by + box, b.get() ? Theme.accent : Theme.PANEL_LIGHT);
            ctx.drawBorder(bx, by, box, box, Theme.OUTLINE);
        } else if (s instanceof NumberSetting n) {
            ctx.drawText(textRenderer, s.getName() + ": " + formatNumber(n.get()), indent, r.y + 2, Theme.TEXT_DIM, false);
            int trackX = indent;
            int trackW = r.x + r.w - 8 - trackX;
            int trackY = r.y + r.h - 6;
            ctx.fill(trackX, trackY, trackX + trackW, trackY + 3, Theme.PANEL_LIGHT);
            int fill = (int) Math.round(trackW * n.getFraction());
            ctx.fill(trackX, trackY, trackX + fill, trackY + 3, Theme.accent);
        } else if (s instanceof ModeSetting m) {
            ctx.drawText(textRenderer, s.getName(), indent, r.y + 2, Theme.TEXT_DIM, false);
            String value = m.get();
            int vw = textRenderer.getWidth(value);
            ctx.drawText(textRenderer, value, r.x + r.w - vw - 6, r.y + 2, Theme.accent, false);
        } else {
            ctx.drawText(textRenderer, s.getName(), indent, r.y + 2, Theme.TEXT_OFF, false);
        }
    }

    // -- input ---------------------------------------------------------

    @Override
    public boolean mouseClicked(double mouseX, double mouseY, int button) {
        for (Row r : layout()) {
            if (!contains(r, mouseX, mouseY)) {
                continue;
            }
            switch (r.kind) {
                case HEADER -> {
                    draggingPanel = r.category;
                    int[] pos = panelPos.get(r.category);
                    dragOffX = (int) mouseX - pos[0];
                    dragOffY = (int) mouseY - pos[1];
                }
                case MODULE -> handleModuleClick(r, mouseX, button);
                case SETTING -> handleSettingClick(r, mouseX, button);
            }
            return true;
        }
        bindingModule = null;
        return super.mouseClicked(mouseX, mouseY, button);
    }

    private void handleModuleClick(Row r, double mouseX, int button) {
        boolean onBadge = mouseX >= r.x + r.w - 30;
        if (button == 1) {
            if (expanded.contains(r.module)) {
                expanded.remove(r.module);
            } else {
                expanded.add(r.module);
            }
        } else if (button == 0) {
            if (onBadge) {
                bindingModule = bindingModule == r.module ? null : r.module;
            } else {
                r.module.toggle();
            }
        }
    }

    private void handleSettingClick(Row r, double mouseX, int button) {
        Setting s = r.setting;
        if (s instanceof BooleanSetting b) {
            b.toggle();
        } else if (s instanceof NumberSetting n) {
            draggingSlider = n;
            sliderX = r.x + 12;
            sliderW = r.x + r.w - 8 - sliderX;
            n.setFraction((mouseX - sliderX) / sliderW);
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
        if (draggingPanel != null) {
            panelPos.put(draggingPanel, new int[]{(int) mouseX - dragOffX, (int) mouseY - dragOffY});
            return true;
        }
        if (draggingSlider != null) {
            draggingSlider.setFraction((mouseX - sliderX) / sliderW);
            return true;
        }
        return super.mouseDragged(mouseX, mouseY, button, dx, dy);
    }

    @Override
    public boolean mouseReleased(double mouseX, double mouseY, int button) {
        draggingPanel = null;
        draggingSlider = null;
        return super.mouseReleased(mouseX, mouseY, button);
    }

    @Override
    public boolean keyPressed(int keyCode, int scanCode, int modifiers) {
        if (bindingModule != null) {
            if (keyCode == GLFW.GLFW_KEY_ESCAPE || keyCode == GLFW.GLFW_KEY_DELETE
                    || keyCode == GLFW.GLFW_KEY_BACKSPACE) {
                bindingModule.setKeyCode(GLFW.GLFW_KEY_UNKNOWN);
            } else {
                bindingModule.setKeyCode(keyCode);
            }
            bindingModule = null;
            return true;
        }
        if (keyCode == Dwine.config.clickGuiKey) {
            close();
            return true;
        }
        return super.keyPressed(keyCode, scanCode, modifiers);
    }

    @Override
    public void close() {
        if (Dwine.config != null) {
            Dwine.config.save();
        }
        super.close();
    }

    @Override
    public boolean shouldPause() {
        return false;
    }

    // -- helpers -------------------------------------------------------

    private static boolean contains(Row r, double mouseX, double mouseY) {
        return mouseX >= r.x && mouseX <= r.x + r.w && mouseY >= r.y && mouseY <= r.y + r.h;
    }

    private static String formatNumber(double v) {
        return v == Math.rint(v) ? String.format("%.0f", v) : String.format("%.2f", v);
    }

    private static String keyName(int key) {
        if (key == GLFW.GLFW_KEY_UNKNOWN) {
            return "-";
        }
        String name = GLFW.glfwGetKeyName(key, 0);
        if (name != null) {
            return name.toUpperCase();
        }
        return switch (key) {
            case GLFW.GLFW_KEY_SPACE -> "SPACE";
            case GLFW.GLFW_KEY_LEFT_SHIFT -> "LSHIFT";
            case GLFW.GLFW_KEY_RIGHT_SHIFT -> "RSHIFT";
            case GLFW.GLFW_KEY_LEFT_CONTROL -> "LCTRL";
            case GLFW.GLFW_KEY_RIGHT_CONTROL -> "RCTRL";
            case GLFW.GLFW_KEY_LEFT_ALT -> "LALT";
            case GLFW.GLFW_KEY_TAB -> "TAB";
            case GLFW.GLFW_KEY_ENTER -> "ENTER";
            default -> "K" + key;
        };
    }
}
