package com.dwine;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.Minecraft;
import net.minecraft.resources.Identifier;

/** Native 26.2 Dwine feature state, persistence, HUD and lightweight client effects. */
public final class DwineFeatures {
    public static final DwineFeatures INSTANCE = new DwineFeatures();

    private final LinkedHashMap<String, Boolean> features = new LinkedHashMap<>();
    private final Path configFile = FabricLoader.getInstance().getConfigDir().resolve("dwine/features-26.2.properties");
    private Double savedGamma;
    private Integer savedFov;
    private Boolean savedBob;

    private DwineFeatures() {
        features.put("Watermark", true);
        features.put("FPS", true);
        features.put("Coordinates", true);
        features.put("Keystrokes", true);
        features.put("Fullbright", false);
        features.put("Zoom", false);
        features.put("No Bobbing", false);
        features.put("Auto Sprint", false);
        features.put("Toggle Sprint", false);
        features.put("Toggle Sneak", false);
        load();
    }

    public Map<String, Boolean> all() {
        return Map.copyOf(features);
    }

    public boolean enabled(String name) {
        return features.getOrDefault(name, false);
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
            if (enabled("Watermark")) {
                graphics.text(mc.font, "Dwine 26.2", 8, y, 0xFF8B7CFF, true);
                y += 12;
            }
            if (enabled("FPS")) {
                graphics.text(mc.font, "FPS: " + mc.getFps(), 8, y, 0xFFFFFFFF, true);
                y += 11;
            }
            if (enabled("Coordinates")) {
                graphics.text(mc.font, String.format("XYZ: %.1f / %.1f / %.1f", mc.player.getX(), mc.player.getY(), mc.player.getZ()), 8, y, 0xFFFFFFFF, true);
                y += 11;
            }
            if (enabled("Keystrokes")) {
                String keys = (mc.options.keyUp.isDown() ? "[W] " : " W  ")
                        + (mc.options.keyLeft.isDown() ? "[A] " : " A  ")
                        + (mc.options.keyDown.isDown() ? "[S] " : " S  ")
                        + (mc.options.keyRight.isDown() ? "[D]" : " D ");
                graphics.text(mc.font, keys, 8, y, 0xFFFFFFFF, true);
            }
        });
    }

    public void tick(Minecraft mc, boolean zoomHeld) {
        if (mc.player == null) return;

        if (enabled("Fullbright")) {
            if (savedGamma == null) savedGamma = mc.options.gamma().get();
            mc.options.gamma().set(16.0);
        } else if (savedGamma != null) {
            mc.options.gamma().set(savedGamma);
            savedGamma = null;
        }

        if (enabled("No Bobbing")) {
            if (savedBob == null) savedBob = mc.options.bobView().get();
            mc.options.bobView().set(false);
        } else if (savedBob != null) {
            mc.options.bobView().set(savedBob);
            savedBob = null;
        }

        if (enabled("Zoom") && zoomHeld) {
            if (savedFov == null) savedFov = mc.options.fov().get();
            mc.options.fov().set(30);
        } else if (savedFov != null) {
            mc.options.fov().set(savedFov);
            savedFov = null;
        }

        if (enabled("Auto Sprint") && mc.options.keyUp.isDown()) {
            mc.player.setSprinting(true);
        }
    }

    private void load() {
        if (!Files.exists(configFile)) return;
        Properties p = new Properties();
        try (InputStream in = Files.newInputStream(configFile)) {
            p.load(in);
            for (String key : features.keySet()) {
                if (p.containsKey(key)) features.put(key, Boolean.parseBoolean(p.getProperty(key)));
            }
        } catch (IOException ignored) { }
    }

    private void save() {
        try {
            Files.createDirectories(configFile.getParent());
            Properties p = new Properties();
            features.forEach((k, v) -> p.setProperty(k, Boolean.toString(v)));
            try (OutputStream out = Files.newOutputStream(configFile)) {
                p.store(out, "Dwine 26.2 features");
            }
        } catch (IOException e) {
            DwineClient.LOGGER.warn("Could not save Dwine configuration", e);
        }
    }
}
