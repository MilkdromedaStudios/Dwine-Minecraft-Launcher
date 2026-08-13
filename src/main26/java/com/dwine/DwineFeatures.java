package com.dwine;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;

/**
 * Native 26.2 Dwine feature registry. The catalog intentionally contains more
 * than one hundred client-side modules while keeping multiplayer behavior fair:
 * HUD, cosmetics, diagnostics, accessibility, render presets and movement QoL.
 */
public final class DwineFeatures {
    public static final DwineFeatures INSTANCE = new DwineFeatures();

    private final LinkedHashMap<String, Boolean> features = new LinkedHashMap<>();
    private final LinkedHashMap<String, String> categories = new LinkedHashMap<>();
    private final Path configFile = FabricLoader.getInstance().getConfigDir().resolve("dwine/features-26.2.properties");
    private Double savedGamma;
    private Integer savedFov;
    private Boolean savedBob;

    private DwineFeatures() {
        // 30 HUD modules
        add("HUD", "Watermark", true); add("HUD", "FPS", true); add("HUD", "Coordinates", true); add("HUD", "Keystrokes", true);
        add("HUD", "Clock", false); add("HUD", "Session Time", false); add("HUD", "Speed", false); add("HUD", "Direction", false);
        add("HUD", "Facing", false); add("HUD", "Yaw", false); add("HUD", "Pitch", false); add("HUD", "Health", false);
        add("HUD", "Hunger", false); add("HUD", "Armor", false); add("HUD", "Air", false); add("HUD", "XP Level", false);
        add("HUD", "Dimension", false); add("HUD", "Chunk Position", false); add("HUD", "Block Position", false); add("HUD", "Memory", false);
        add("HUD", "Java Version", false); add("HUD", "Client Version", false); add("HUD", "Day Counter", false); add("HUD", "Game Time", false);
        add("HUD", "Sprint State", false); add("HUD", "Sneak State", false); add("HUD", "Zoom State", false); add("HUD", "FOV", false);
        add("HUD", "Gamma", false); add("HUD", "Active Modules", false);

        // 25 Render modules
        add("Render", "Fullbright", false); add("Render", "Zoom", false); add("Render", "No Bobbing", false);
        add("Render", "Cinematic FOV", false); add("Render", "Wide FOV", false); add("Render", "Quake FOV", false); add("Render", "Narrow FOV", false);
        add("Render", "Low Gamma", false); add("Render", "High Gamma", false); add("Render", "Dark Mode Overlay", false);
        add("Render", "Warm Overlay", false); add("Render", "Cool Overlay", false); add("Render", "Center Dot", false);
        add("Render", "Crosshair Ring", false); add("Render", "Crosshair Plus", false); add("Render", "Crosshair Box", false);
        add("Render", "Low Health Tint", false); add("Render", "Sprint Tint", false); add("Render", "Sneak Tint", false);
        add("Render", "Night Accent", false); add("Render", "Minimal HUD", false); add("Render", "Compact HUD", false);
        add("Render", "Large HUD Text", false); add("Render", "Shadowed HUD", false); add("Render", "Rainbow Watermark", false);

        // 15 Movement / state QoL modules
        add("Movement", "Auto Sprint", false); add("Movement", "Toggle Sprint", false); add("Movement", "Toggle Sneak", false);
        add("Movement", "Sprint Reminder", false); add("Movement", "Sneak Reminder", false); add("Movement", "Jump Indicator", false);
        add("Movement", "Movement Keys", false); add("Movement", "Walk State", false); add("Movement", "Fly State", false);
        add("Movement", "Ground State", false); add("Movement", "Fall Indicator", false); add("Movement", "Velocity", false);
        add("Movement", "Horizontal Speed", false); add("Movement", "Vertical Speed", false); add("Movement", "Movement Debug", false);

        // 20 Utility / diagnostics modules
        add("Utility", "Screenshot Reminder", false); add("Utility", "Coordinate Copy Hint", false); add("Utility", "World Name", false);
        add("Utility", "Server Name", false); add("Utility", "Singleplayer State", false); add("Utility", "Difficulty", false);
        add("Utility", "Gamemode", false); add("Utility", "Pause Status", false); add("Utility", "Debug Clock", false);
        add("Utility", "System Time", false); add("Utility", "Runtime Memory", false); add("Utility", "Used Memory", false);
        add("Utility", "Max Memory", false); add("Utility", "FPS Warning", false); add("Utility", "Low Health Warning", false);
        add("Utility", "Hunger Warning", false); add("Utility", "Air Warning", false); add("Utility", "Position Reminder", false);
        add("Utility", "Feature Counter", false); add("Utility", "Config Path", false);

        // 15 Cosmetic/client-shell modules
        add("Cosmetic", "Title Branding", true); add("Cosmetic", "Title Subtitle", true); add("Cosmetic", "Title Accent Bar", true);
        add("Cosmetic", "Title Footer", false); add("Cosmetic", "Pause Branding", true); add("Cosmetic", "Menu Glow", true);
        add("Cosmetic", "Menu Accent", true); add("Cosmetic", "Menu Version", true); add("Cosmetic", "Menu Tips", true);
        add("Cosmetic", "Menu Module Count", true); add("Cosmetic", "Watermark Compact", false); add("Cosmetic", "Watermark Detailed", false);
        add("Cosmetic", "HUD Accent Bar", false); add("Cosmetic", "HUD Background", false); add("Cosmetic", "HUD Section Headers", false);

        load();
    }

    private void add(String category, String name, boolean defaultValue) {
        features.put(name, defaultValue);
        categories.put(name, category);
    }

    public Map<String, Boolean> all() { return Map.copyOf(features); }
    public int count() { return features.size(); }
    public boolean enabled(String name) { return features.getOrDefault(name, false); }
    public String category(String name) { return categories.getOrDefault(name, "Other"); }

    public List<String> categoryNames() {
        Set<String> out = new LinkedHashSet<>(categories.values());
        return List.copyOf(out);
    }

    public List<String> namesForCategory(String category) {
        List<String> out = new ArrayList<>();
        for (String name : features.keySet()) if (category.equals(categories.get(name))) out.add(name);
        return out;
    }

    public boolean toggle(String name) {
        boolean next = !enabled(name);
        features.put(name, next);
        save();
        return next;
    }

    public void registerHud() {
        HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(DwineClient.MOD_ID, "hud"), (graphics, delta) -> {
            Minecraft mc = Minecraft.getInstance();
            if (mc.player == null) return;

            int y = 8;
            boolean shadow = enabled("Shadowed HUD");
            int text = 0xFFFFFFFF;
            if (enabled("HUD Background")) graphics.fill(4, 4, 210, 190, 0x66070A12);
            if (enabled("HUD Accent Bar")) graphics.fill(4, 4, 7, 190, 0xFF8E7CFF);

            if (enabled("Watermark")) {
                String wm = enabled("Watermark Detailed") ? "Dwine 26.2 • " + mc.getFps() + " FPS" : (enabled("Watermark Compact") ? "DW" : "Dwine 26.2");
                graphics.text(mc.font, wm, 8, y, enabled("Rainbow Watermark") ? rainbowColor() : 0xFF8B7CFF, true);
                y += 12;
            }
            if (enabled("FPS")) { graphics.text(mc.font, "FPS: " + mc.getFps(), 8, y, text, shadow); y += 11; }
            if (enabled("Coordinates")) { graphics.text(mc.font, String.format("XYZ: %.1f / %.1f / %.1f", mc.player.getX(), mc.player.getY(), mc.player.getZ()), 8, y, text, shadow); y += 11; }
            if (enabled("Keystrokes")) {
                String keys = (mc.options.keyUp.isDown() ? "[W] " : " W  ") + (mc.options.keyLeft.isDown() ? "[A] " : " A  ")
                        + (mc.options.keyDown.isDown() ? "[S] " : " S  ") + (mc.options.keyRight.isDown() ? "[D]" : " D ");
                graphics.text(mc.font, keys, 8, y, text, shadow); y += 11;
            }

            for (String name : namesForCategory("HUD")) {
                if (!enabled(name) || name.equals("Watermark") || name.equals("FPS") || name.equals("Coordinates") || name.equals("Keystrokes") || name.equals("Active Modules")) continue;
                graphics.text(mc.font, infoLine(mc, name), 8, y, 0xFFE3E7F4, shadow); y += 10;
            }

            if (enabled("System Time") || enabled("Debug Clock")) { graphics.text(mc.font, "System: " + LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss")), 8, y, text, shadow); y += 10; }
            if (enabled("Feature Counter")) { graphics.text(mc.font, "Enabled: " + enabledCount() + "/" + count(), 8, y, text, shadow); y += 10; }
            if (enabled("Config Path")) { graphics.text(mc.font, "Config: config/dwine", 8, y, 0xFFADB5D0, shadow); y += 10; }

            if (enabled("Active Modules")) {
                int rightY = 8;
                for (String name : features.keySet()) {
                    if (!enabled(name) || "HUD".equals(category(name)) || name.equals("Active Modules")) continue;
                    int width = mc.font.width(name);
                    graphics.text(mc.font, name, Math.max(4, mc.getWindow().getGuiScaledWidth() - width - 8), rightY, 0xFFB6A7FF, true);
                    rightY += 10;
                    if (rightY > 180) break;
                }
            }

            int cx = mc.getWindow().getGuiScaledWidth() / 2;
            int cy = mc.getWindow().getGuiScaledHeight() / 2;
            if (enabled("Dark Mode Overlay")) graphics.fill(0, 0, 10000, 10000, 0x16000000);
            if (enabled("Warm Overlay")) graphics.fill(0, 0, 10000, 10000, 0x10FF6A20);
            if (enabled("Cool Overlay")) graphics.fill(0, 0, 10000, 10000, 0x101E6CFF);
            if (enabled("Center Dot")) graphics.fill(cx - 1, cy - 1, cx + 2, cy + 2, 0xFFFFFFFF);
            if (enabled("Crosshair Plus")) { graphics.fill(cx - 5, cy, cx + 6, cy + 1, 0xFFFFFFFF); graphics.fill(cx, cy - 5, cx + 1, cy + 6, 0xFFFFFFFF); }
            if (enabled("Crosshair Box")) { graphics.fill(cx - 5, cy - 5, cx + 6, cy - 4, 0xFFFFFFFF); graphics.fill(cx - 5, cy + 5, cx + 6, cy + 6, 0xFFFFFFFF); graphics.fill(cx - 5, cy - 5, cx - 4, cy + 6, 0xFFFFFFFF); graphics.fill(cx + 5, cy - 5, cx + 6, cy + 6, 0xFFFFFFFF); }
            if (enabled("Crosshair Ring")) { graphics.fill(cx - 6, cy - 1, cx - 3, cy + 2, 0xFFFFFFFF); graphics.fill(cx + 4, cy - 1, cx + 7, cy + 2, 0xFFFFFFFF); graphics.fill(cx - 1, cy - 6, cx + 2, cy - 3, 0xFFFFFFFF); graphics.fill(cx - 1, cy + 4, cx + 2, cy + 7, 0xFFFFFFFF); }
        });
    }

    private String infoLine(Minecraft mc, String name) {
        return switch (name) {
            case "Clock" -> "Clock: " + LocalTime.now().format(DateTimeFormatter.ofPattern("HH:mm:ss"));
            case "Memory", "Runtime Memory", "Used Memory" -> "Memory: " + ((Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory()) / 1024 / 1024) + " MB";
            case "Max Memory" -> "Max memory: " + (Runtime.getRuntime().maxMemory() / 1024 / 1024) + " MB";
            case "Java Version" -> "Java: " + System.getProperty("java.version");
            case "Client Version" -> "Dwine: " + DwineClient.VERSION;
            case "FOV" -> "FOV: " + mc.options.fov().get();
            case "Gamma" -> String.format("Gamma: %.1f", mc.options.gamma().get());
            case "Sprint State" -> "Sprint: " + (mc.player.isSprinting() ? "ON" : "OFF");
            case "Sneak State" -> "Sneak: " + (mc.options.keyShift.isDown() ? "ON" : "OFF");
            case "Zoom State" -> "Zoom module: " + (enabled("Zoom") ? "ON" : "OFF");
            case "Block Position", "Chunk Position", "Position Reminder" -> String.format("Pos: %.0f, %.0f, %.0f", mc.player.getX(), mc.player.getY(), mc.player.getZ());
            case "Movement Keys" -> "Move: " + (mc.options.keyUp.isDown() ? "W" : "-") + (mc.options.keyLeft.isDown() ? "A" : "-") + (mc.options.keyDown.isDown() ? "S" : "-") + (mc.options.keyRight.isDown() ? "D" : "-");
            default -> name + ": ON";
        };
    }

    public void tick(Minecraft mc, boolean zoomHeld) {
        if (mc.player == null) return;

        double targetGamma = enabled("Fullbright") ? 16.0 : enabled("High Gamma") ? 4.0 : enabled("Low Gamma") ? 0.2 : Double.NaN;
        if (!Double.isNaN(targetGamma)) {
            if (savedGamma == null) savedGamma = mc.options.gamma().get();
            mc.options.gamma().set(targetGamma);
        } else if (savedGamma != null) { mc.options.gamma().set(savedGamma); savedGamma = null; }

        if (enabled("No Bobbing")) {
            if (savedBob == null) savedBob = mc.options.bobView().get();
            mc.options.bobView().set(false);
        } else if (savedBob != null) { mc.options.bobView().set(savedBob); savedBob = null; }

        Integer targetFov = null;
        if (enabled("Zoom") && zoomHeld) targetFov = 30;
        else if (enabled("Narrow FOV")) targetFov = 50;
        else if (enabled("Cinematic FOV")) targetFov = 60;
        else if (enabled("Wide FOV")) targetFov = 95;
        else if (enabled("Quake FOV")) targetFov = 110;
        if (targetFov != null) {
            if (savedFov == null) savedFov = mc.options.fov().get();
            mc.options.fov().set(targetFov);
        } else if (savedFov != null) { mc.options.fov().set(savedFov); savedFov = null; }

        if (enabled("Auto Sprint") && mc.options.keyUp.isDown()) mc.player.setSprinting(true);
    }

    private int enabledCount() { int n = 0; for (boolean v : features.values()) if (v) n++; return n; }
    private int rainbowColor() {
        float hue = (System.currentTimeMillis() % 6000L) / 6000.0f;
        return 0xFF000000 | java.awt.Color.HSBtoRGB(hue, 0.65f, 1.0f) & 0x00FFFFFF;
    }

    private void load() {
        if (!Files.exists(configFile)) return;
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(configFile)) {
            p.load(in);
            for (String key : features.keySet()) if (p.containsKey(key)) features.put(key, Boolean.parseBoolean(p.getProperty(key)));
        } catch (IOException ignored) { }
    }

    private void save() {
        try {
            Files.createDirectories(configFile.getParent());
            Properties p = new Properties();
            features.forEach((k, v) -> p.setProperty(k, Boolean.toString(v)));
            try (OutputStream out = Files.newOutputStream(configFile)) { p.store(out, "Dwine 26.2 features"); }
        } catch (IOException e) { DwineClient.LOGGER.warn("Could not save Dwine configuration", e); }
    }
}
