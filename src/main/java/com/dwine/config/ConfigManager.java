package com.dwine.config;

import com.dwine.Dwine;
import com.dwine.gui.Theme;
import com.dwine.module.HudModule;
import com.dwine.module.Module;
import com.dwine.setting.Setting;
import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.fabricmc.loader.api.FabricLoader;
import org.lwjgl.glfw.GLFW;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * Reads and writes {@code config/dwine/features.json} — the single file the
 * Python Dwine launcher and this mod both speak. The launcher can pre-seed
 * which modules are on and their settings before the game starts; the mod
 * loads those, lets the player tweak them in-game, and writes them back.
 */
public class ConfigManager {
    private static final Logger LOGGER = LoggerFactory.getLogger("dwine-config");
    private static final int SCHEMA = 1;

    private final Gson gson = new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create();
    private final Path file;

    public int clickGuiKey = GLFW.GLFW_KEY_RIGHT_SHIFT;
    public int hudEditorKey = GLFW.GLFW_KEY_RIGHT_CONTROL;

    public ConfigManager() {
        this.file = FabricLoader.getInstance().getConfigDir().resolve("dwine").resolve("features.json");
    }

    // -- load ----------------------------------------------------------

    public void load() {
        if (!Files.exists(file)) {
            save(); // materialise defaults so the launcher has something to edit
            return;
        }
        try (Reader reader = Files.newBufferedReader(file, StandardCharsets.UTF_8)) {
            JsonElement parsed = JsonParser.parseReader(reader);
            if (!parsed.isJsonObject()) {
                return;
            }
            apply(parsed.getAsJsonObject());
        } catch (IOException | RuntimeException e) {
            LOGGER.warn("Could not read {} — using defaults ({})", file, e.toString());
        }
    }

    private void apply(JsonObject root) {
        if (root.has("clickGuiKey")) {
            clickGuiKey = root.get("clickGuiKey").getAsInt();
        }
        if (root.has("hudEditorKey")) {
            hudEditorKey = root.get("hudEditorKey").getAsInt();
        }
        if (root.has("accentColor")) {
            try {
                Theme.accent = root.get("accentColor").getAsInt();
                Theme.accentSoft = Theme.withAlpha(Theme.accent, 0x80);
            } catch (RuntimeException ignored) {
            }
        }
        if (!root.has("modules") || !root.get("modules").isJsonObject()) {
            return;
        }
        JsonObject modules = root.getAsJsonObject("modules");
        for (Module module : Dwine.modules.getModules()) {
            if (!modules.has(module.getName())) {
                continue;
            }
            JsonObject entry = modules.getAsJsonObject(module.getName());
            if (entry.has("enabled")) {
                module.setEnabledQuiet(entry.get("enabled").getAsBoolean());
            }
            if (entry.has("key")) {
                module.setKeyCode(entry.get("key").getAsInt());
            }
            if (module instanceof HudModule hud && entry.has("x") && entry.has("y")) {
                hud.setPosition(entry.get("x").getAsInt(), entry.get("y").getAsInt());
            }
            if (entry.has("settings") && entry.get("settings").isJsonObject()) {
                JsonObject settings = entry.getAsJsonObject("settings");
                for (Setting setting : module.getSettings()) {
                    if (settings.has(setting.getName())) {
                        setting.read(settings.get(setting.getName()));
                    }
                }
            }
        }
    }

    // -- save ----------------------------------------------------------

    public void save() {
        JsonObject root = new JsonObject();
        root.addProperty("schemaVersion", SCHEMA);
        root.addProperty("generatedBy", Dwine.NAME + " mod " + Dwine.VERSION);
        root.addProperty("clickGuiKey", clickGuiKey);
        root.addProperty("hudEditorKey", hudEditorKey);
        root.addProperty("accentColor", Theme.accent);

        JsonObject modules = new JsonObject();
        for (Module module : Dwine.modules.getModules()) {
            JsonObject entry = new JsonObject();
            entry.addProperty("category", module.getCategory().getTitle());
            entry.addProperty("enabled", module.isEnabled());
            entry.addProperty("key", module.getKeyCode());
            entry.addProperty("description", module.getDescription());
            if (module instanceof HudModule hud) {
                entry.addProperty("x", hud.getX());
                entry.addProperty("y", hud.getY());
            }
            JsonObject settings = new JsonObject();
            for (Setting setting : module.getSettings()) {
                settings.add(setting.getName(), setting.write());
            }
            entry.add("settings", settings);
            modules.add(module.getName(), entry);
        }
        root.add("modules", modules);

        try {
            Files.createDirectories(file.getParent());
            try (Writer writer = Files.newBufferedWriter(file, StandardCharsets.UTF_8)) {
                gson.toJson(root, writer);
            }
        } catch (IOException e) {
            LOGGER.error("Could not write {} ({})", file, e.toString());
        }
    }
}
