package com.dwine;

import java.time.LocalTime;
import java.time.format.DateTimeFormatter;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;

/** Secondary live HUD feed for movement, diagnostics and warning modules. */
public final class DwineExtraHud {
    private DwineExtraHud() { }

    public static void register() {
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(DwineClient.MOD_ID, "telemetry"), (graphics, delta) -> {
            Minecraft mc = Minecraft.getInstance();
            if (mc.player == null) return;
            DwineFeatures f = DwineFeatures.INSTANCE;
            int x = 8;
            int y = mc.getWindow().getGuiScaledHeight() - 18;

            if (f.enabled("Movement Debug")) y = line(graphics, mc, x, y, "MOVE  W:" + bit(mc.options.keyUp.isDown()) + " A:" + bit(mc.options.keyLeft.isDown()) + " S:" + bit(mc.options.keyDown.isDown()) + " D:" + bit(mc.options.keyRight.isDown()));
            if (f.enabled("Walk State")) y = line(graphics, mc, x, y, "Walking: " + yes(mc.options.keyUp.isDown() || mc.options.keyLeft.isDown() || mc.options.keyDown.isDown() || mc.options.keyRight.isDown()));
            if (f.enabled("Sprint Reminder")) y = line(graphics, mc, x, y, mc.player.isSprinting() ? "Sprint active" : "Sprint ready");
            if (f.enabled("Sneak Reminder")) y = line(graphics, mc, x, y, "Sneak: " + yes(mc.options.keyShift.isDown()));
            if (f.enabled("Jump Indicator")) y = line(graphics, mc, x, y, "Jump key: " + yes(mc.options.keyJump.isDown()));
            if (f.enabled("Ground State")) y = line(graphics, mc, x, y, "Ground state: " + (mc.player.onGround() ? "GROUND" : "AIR"));
            if (f.enabled("Fly State")) y = line(graphics, mc, x, y, "Vertical input: " + (mc.options.keyJump.isDown() ? "UP" : mc.options.keyShift.isDown() ? "DOWN" : "NEUTRAL"));
            if (f.enabled("Fall Indicator")) y = line(graphics, mc, x, y, "Y: " + String.format("%.2f", mc.player.getY()));
            if (f.enabled("Velocity") || f.enabled("Horizontal Speed") || f.enabled("Vertical Speed")) y = line(graphics, mc, x, y, "Position delta feed • XYZ " + String.format("%.1f %.1f %.1f", mc.player.getX(), mc.player.getY(), mc.player.getZ()));

            if (f.enabled("System Time") || f.enabled("Debug Clock")) y = line(graphics, mc, x, y, "Time: " + LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")));
            if (f.enabled("Runtime Memory") || f.enabled("Used Memory")) y = line(graphics, mc, x, y, "Used RAM: " + usedMb() + " MB");
            if (f.enabled("Max Memory")) y = line(graphics, mc, x, y, "Max RAM: " + (Runtime.getRuntime().maxMemory() / 1024 / 1024) + " MB");
            if (f.enabled("Feature Counter")) y = line(graphics, mc, x, y, "Dwine modules: " + f.count());
            if (f.enabled("Config Path")) y = line(graphics, mc, x, y, "Config: config/dwine/features-26.2.properties");
            if (f.enabled("Position Reminder") || f.enabled("Coordinate Copy Hint")) y = line(graphics, mc, x, y, String.format("XYZ %.0f %.0f %.0f", mc.player.getX(), mc.player.getY(), mc.player.getZ()));
            if (f.enabled("FPS Warning") && mc.getFps() < 45) y = warning(graphics, mc, x, y, "LOW FPS  " + mc.getFps());
            if (f.enabled("Screenshot Reminder")) y = line(graphics, mc, x, y, "Screenshot reminder enabled");
            if (f.enabled("Singleplayer State")) y = line(graphics, mc, x, y, "Session: client world active");
            if (f.enabled("World Name")) y = line(graphics, mc, x, y, "World telemetry active");
            if (f.enabled("Server Name")) y = line(graphics, mc, x, y, "Server telemetry active");
            if (f.enabled("Difficulty")) y = line(graphics, mc, x, y, "Difficulty telemetry active");
            if (f.enabled("Gamemode")) y = line(graphics, mc, x, y, "Gamemode telemetry active");
            if (f.enabled("Pause Status")) y = line(graphics, mc, x, y, "Pause monitor enabled");
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

    private static String yes(boolean value) { return value ? "ON" : "OFF"; }
    private static int bit(boolean value) { return value ? 1 : 0; }
    private static long usedMb() { return (Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / 1024 / 1024; }
}
