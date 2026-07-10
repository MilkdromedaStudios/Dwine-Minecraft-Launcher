package com.dwine.module;

import com.dwine.setting.Setting;
import net.minecraft.client.MinecraftClient;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.List;

/**
 * A single toggleable client feature. Everything a Dwine module does is
 * client-side, cosmetic or quality-of-life — nothing here touches packets or
 * changes what the server sees.
 */
public abstract class Module {
    protected static final MinecraftClient mc = MinecraftClient.getInstance();

    private final String name;
    private final String description;
    private final Category category;

    private final List<Setting> settings = new ArrayList<>();

    private boolean enabled;
    private int keyCode = GLFW.GLFW_KEY_UNKNOWN;
    private boolean holdKey;

    protected Module(String name, String description, Category category) {
        this.name = name;
        this.description = description;
        this.category = category;
    }

    /**
     * Hold-key modules (e.g. Zoom) use their bound key as a momentary "while
     * held" trigger instead of an on/off toggle, so the toggle dispatcher
     * skips them and the module reads the key itself.
     */
    public boolean isHoldKey() {
        return holdKey;
    }

    protected void markHoldKey() {
        this.holdKey = true;
    }

    /** True while this module's bound key is physically held down. */
    protected boolean isKeyHeld() {
        if (keyCode == GLFW.GLFW_KEY_UNKNOWN || mc.getWindow() == null) {
            return false;
        }
        return net.minecraft.client.util.InputUtil.isKeyPressed(mc.getWindow().getHandle(), keyCode);
    }

    // -- registration helpers ------------------------------------------

    protected <T extends Setting> T add(T setting) {
        settings.add(setting);
        return setting;
    }

    // -- lifecycle -----------------------------------------------------

    public void toggle() {
        setEnabled(!enabled);
    }

    public void setEnabled(boolean enabled) {
        if (this.enabled == enabled) {
            return;
        }
        this.enabled = enabled;
        if (enabled) {
            onEnable();
        } else {
            onDisable();
        }
    }

    /** Called once, at load, for modules that start enabled. */
    public void onLoad() {
        if (enabled) {
            onEnable();
        }
    }

    protected void onEnable() {
    }

    protected void onDisable() {
    }

    /** Runs every client tick while the game is in a world. */
    public void onTick() {
    }

    // -- accessors -----------------------------------------------------

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    public Category getCategory() {
        return category;
    }

    public boolean isEnabled() {
        return enabled;
    }

    /** Sets the enabled flag without firing enable/disable (used when loading config). */
    public void setEnabledQuiet(boolean enabled) {
        this.enabled = enabled;
    }

    public int getKeyCode() {
        return keyCode;
    }

    public void setKeyCode(int keyCode) {
        this.keyCode = keyCode;
    }

    public List<Setting> getSettings() {
        return settings;
    }
}
