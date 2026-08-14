package com.dwine;

import java.lang.reflect.Method;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;

/** Completes visual, warning, and cosmetic module behavior without depending on unstable mapped entity accessors. */
public final class DwineVisualRuntime {
    private DwineVisualRuntime() { }

    public static void register() {
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(DwineClient.MOD_ID, "visual_runtime"), (g, delta) -> {
            Minecraft mc = Minecraft.getInstance();
            if (mc.player == null) return;
            DwineFeatures f = DwineFeatures.INSTANCE;
            int w = mc.getWindow().getGuiScaledWidth();
            int h = mc.getWindow().getGuiScaledHeight();

            double health = number(mc.player, "getHealth", -1);
            double maxHealth = number(mc.player, "getMaxHealth", 20);
            double hunger = nestedNumber(mc.player, "getFoodData", "getFoodLevel", -1);
            double air = number(mc.player, "getAirSupply", -1);
            double armor = number(mc.player, "getArmorValue", -1);

            if (f.enabled("Low Health Tint") && health >= 0 && maxHealth > 0 && health / maxHealth < 0.35) {
                g.fill(0, 0, w, 7, 0xAAE13C58); g.fill(0, h - 7, w, h, 0xAAE13C58);
                g.fill(0, 0, 7, h, 0xAAE13C58); g.fill(w - 7, 0, w, h, 0xAAE13C58);
            }
            if (f.enabled("Sprint Tint") && mc.player.isSprinting()) g.fill(0, 0, w, h, 0x0C63D5FF);
            if (f.enabled("Sneak Tint") && mc.options.keyShift.isDown()) g.fill(0, 0, w, h, 0x0C9B7CFF);
            if (f.enabled("Night Accent")) {
                g.fill(0, 0, w, 2, 0xFF6659C9); g.fill(0, h - 2, w, h, 0xFF6659C9);
            }

            if (f.enabled("Minimal HUD")) g.fill(6, 6, 84, 8, 0xFF8E7CFF);
            if (f.enabled("Compact HUD")) g.fill(w - 56, 6, w - 6, 8, 0xFF8E7CFF);
            if (f.enabled("Large HUD Text")) g.text(mc.font, "DWINE", w / 2 - 18, 8, 0x88C7BCFF, true);
            if (f.enabled("HUD Section Headers")) g.text(mc.font, "CLIENT TELEMETRY", 8, Math.max(8, h - 112), 0xFF8E7CFF, true);

            int warnY = 16;
            if (f.enabled("Low Health Warning") && health >= 0 && maxHealth > 0 && health / maxHealth < 0.35)
                warnY = banner(g, mc, w, warnY, "LOW HEALTH  " + fmt(health) + "/" + fmt(maxHealth), 0xCCE13C58);
            if (f.enabled("Hunger Warning") && hunger >= 0 && hunger <= 6)
                warnY = banner(g, mc, w, warnY, "LOW HUNGER  " + (int) hunger + "/20", 0xCCDB8B35);
            if (f.enabled("Air Warning") && air >= 0 && air <= 90)
                warnY = banner(g, mc, w, warnY, "LOW AIR  " + (int) air, 0xCC3B89D6);

            int statY = h - 8;
            if (f.enabled("Health")) statY = stat(g, mc, statY, health >= 0 ? "Health " + fmt(health) + "/" + fmt(maxHealth) : "Health unavailable");
            if (f.enabled("Hunger")) statY = stat(g, mc, statY, hunger >= 0 ? "Hunger " + (int) hunger + "/20" : "Hunger unavailable");
            if (f.enabled("Armor")) statY = stat(g, mc, statY, armor >= 0 ? "Armor " + (int) armor : "Armor unavailable");
            if (f.enabled("Air")) statY = stat(g, mc, statY, air >= 0 ? "Air " + (int) air : "Air unavailable");

            if (f.enabled("Pause Branding") && f.enabled("Active Modules")) {
                g.text(mc.font, "Dwine 0.7", w - mc.font.width("Dwine 0.7") - 8, h - 12, 0xFF8E7CFF, true);
            }
        });
    }

    private static int banner(net.minecraft.client.gui.GuiGraphicsExtractor g, Minecraft mc, int screenW, int y, String text, int bg) {
        int tw = mc.font.width(text);
        int x = (screenW - tw) / 2;
        g.fill(x - 7, y - 4, x + tw + 7, y + 11, bg);
        g.text(mc.font, text, x, y, 0xFFFFFFFF, true);
        return y + 18;
    }

    private static int stat(net.minecraft.client.gui.GuiGraphicsExtractor g, Minecraft mc, int y, String text) {
        int x = mc.getWindow().getGuiScaledWidth() - mc.font.width(text) - 8;
        g.text(mc.font, text, x, y, 0xFFE3E7F4, true);
        return y - 10;
    }

    private static double number(Object target, String method, double fallback) {
        try {
            Method m = target.getClass().getMethod(method);
            Object value = m.invoke(target);
            return value instanceof Number n ? n.doubleValue() : fallback;
        } catch (ReflectiveOperationException ignored) { return fallback; }
    }

    private static double nestedNumber(Object target, String first, String second, double fallback) {
        try {
            Object nested = target.getClass().getMethod(first).invoke(target);
            return nested == null ? fallback : number(nested, second, fallback);
        } catch (ReflectiveOperationException ignored) { return fallback; }
    }

    private static String fmt(double value) { return String.format("%.1f", value); }
}
