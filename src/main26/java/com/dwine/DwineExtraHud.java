package com.dwine;

import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;

/** Secondary live HUD feed for movement, diagnostics and utility modules. */
public final class DwineExtraHud {
    private DwineExtraHud() { }

    public static void register() {
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(DwineClient.MOD_ID, "telemetry"), (graphics, delta) -> {
            Minecraft mc = Minecraft.getInstance();
            if (mc.player == null) return;
            DwineFeatures f = DwineFeatures.INSTANCE;
            int x = 8;
            int y = mc.getWindow().getGuiScaledHeight() - 18;

            if (f.enabled("Movement Debug")) y = line(graphics, mc, x, y, "MOVE W:" + bit(mc.options.keyUp.isDown()) + " A:" + bit(mc.options.keyLeft.isDown()) + " S:" + bit(mc.options.keyDown.isDown()) + " D:" + bit(mc.options.keyRight.isDown()));
            if (f.enabled("Movement Keys")) y = line(graphics, mc, x, y, "Keys " + (mc.options.keyUp.isDown() ? "W" : "-") + (mc.options.keyLeft.isDown() ? "A" : "-") + (mc.options.keyDown.isDown() ? "S" : "-") + (mc.options.keyRight.isDown() ? "D" : "-"));
            if (f.enabled("Walk State")) y = line(graphics, mc, x, y, "Walking: " + yes(mc.options.keyUp.isDown() || mc.options.keyLeft.isDown() || mc.options.keyDown.isDown() || mc.options.keyRight.isDown()));
            if (f.enabled("Sprint Reminder")) y = line(graphics, mc, x, y, mc.player.isSprinting() ? "Sprint active" : "Sprint ready");
            if (f.enabled("Sneak Reminder")) y = line(graphics, mc, x, y, "Sneak: " + yes(mc.options.keyShift.isDown()));
            if (f.enabled("Jump Indicator")) y = line(graphics, mc, x, y, "Jump key: " + yes(mc.options.keyJump.isDown()));
            if (f.enabled("Ground State")) y = line(graphics, mc, x, y, "Ground: " + (mc.player.onGround() ? "YES" : "NO"));
            if (f.enabled("Fly State")) y = line(graphics, mc, x, y, "Vertical input: " + (mc.options.keyJump.isDown() ? "UP" : mc.options.keyShift.isDown() ? "DOWN" : "NEUTRAL"));
            if (f.enabled("Fall Indicator")) y = line(graphics, mc, x, y, "Y: " + String.format("%.2f", mc.player.getY()) + "  vY: " + String.format("%.2f", f.verticalSpeed()));
            if (f.enabled("Velocity")) y = line(graphics, mc, x, y, String.format("Velocity H %.2f  V %.2f b/s", f.horizontalSpeed(), f.verticalSpeed()));
            if (f.enabled("Horizontal Speed")) y = line(graphics, mc, x, y, String.format("Horizontal %.2f b/s", f.horizontalSpeed()));
            if (f.enabled("Vertical Speed")) y = line(graphics, mc, x, y, String.format("Vertical %.2f b/s", f.verticalSpeed()));

            if (f.enabled("System Time") || f.enabled("Debug Clock")) y = line(graphics, mc, x, y, "Time: " + LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")));
            if (f.enabled("Runtime Memory") || f.enabled("Used Memory")) y = line(graphics, mc, x, y, "Used RAM: " + usedMb() + " MB");
            if (f.enabled("Max Memory")) y = line(graphics, mc, x, y, "Max RAM: " + (Runtime.getRuntime().maxMemory() / 1024 / 1024) + " MB");
            if (f.enabled("Feature Counter")) y = line(graphics, mc, x, y, "Dwine catalog: " + f.count() + " modules");
            if (f.enabled("Config Path")) y = line(graphics, mc, x, y, "Config: config/dwine/features-26.2.properties");
            if (f.enabled("Position Reminder") || f.enabled("Coordinate Copy Hint")) y = line(graphics, mc, x, y, String.format("XYZ %.0f %.0f %.0f", mc.player.getX(), mc.player.getY(), mc.player.getZ()));
            if (f.enabled("FPS Warning") && mc.getFps() < 45) y = warning(graphics, mc, x, y, "LOW FPS " + mc.getFps());
            if (f.enabled("Screenshot Reminder")) y = line(graphics, mc, x, y, "Screenshot reminder • use your screenshot key when needed");
            if (f.enabled("Singleplayer State")) y = line(graphics, mc, x, y, "Singleplayer: " + yes(call(mc, "hasSingleplayerServer") instanceof Boolean b && b));
            if (f.enabled("World Name")) y = line(graphics, mc, x, y, "World: " + shortValue(mc.level));
            if (f.enabled("Server Name")) y = line(graphics, mc, x, y, "Server: " + shortValue(call(mc, "getCurrentServer")));
            if (f.enabled("Difficulty")) y = line(graphics, mc, x, y, "Difficulty: " + shortValue(call(mc.level, "getDifficulty")));
            if (f.enabled("Gamemode")) y = line(graphics, mc, x, y, "Gamemode: " + shortValue(call(field(mc, "gameMode"), "getPlayerMode")));
            if (f.enabled("Pause Status")) y = line(graphics, mc, x, y, "Paused: " + yes(call(mc, "isPaused") instanceof Boolean b && b));
        });
    }

    private static int line(net.minecraft.client.gui.GuiGraphicsExtractor g, Minecraft mc, int x, int y, String text) {
        g.text(mc.font, text, x, y, 0xFFD7DDF2, true);
        return y - 10;
    }

    private static int warning(net.minecraft.client.gui.GuiGraphicsExtractor g, Minecraft mc, int x, int y, String text) {
        int w = mc.font.width(text) + 8;
        g.fill(x - 3, y - 2, x + w, y + 10, 0xAA5E2335);
        g.text(mc.font, text, x, y, 0xFFFFA8B7, true);
        return y - 13;
    }

    private static Object call(Object target, String name) {
        if (target == null) return null;
        try { Method m = target.getClass().getMethod(name); return m.invoke(target); }
        catch (ReflectiveOperationException ignored) { return null; }
    }

    private static Object field(Object target, String name) {
        if (target == null) return null;
        try { Field f = target.getClass().getField(name); return f.get(target); }
        catch (ReflectiveOperationException ignored) { return null; }
    }

    private static String shortValue(Object value) {
        if (value == null) return "n/a";
        String s = String.valueOf(value);
        return s.length() > 48 ? s.substring(0, 45) + "..." : s;
    }

    private static String yes(boolean value) { return value ? "YES" : "NO"; }
    private static int bit(boolean value) { return value ? 1 : 0; }
    private static long usedMb() { return (Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / 1024 / 1024; }
}
