package com.dwine;

import com.dwine.config.ConfigManager;
import com.dwine.gui.HudEditorScreen;
import com.dwine.gui.MenuScreen;
import com.dwine.module.Module;
import com.dwine.module.ModuleManager;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.MinecraftClient;
import net.minecraft.client.util.InputUtil;
import org.lwjgl.glfw.GLFW;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.HashSet;
import java.util.Set;

/**
 * Dwine client entrypoint. Wires up the module manager, the shared config,
 * the HUD render callback and raw keyboard handling for the ClickGUI, HUD
 * editor and per-module toggles.
 */
public class DwineClient implements ClientModInitializer {
    public static final Logger LOGGER = LoggerFactory.getLogger("dwine");

    private final Set<Integer> heldLastTick = new HashSet<>();

    @Override
    public void onInitializeClient() {
        LOGGER.info("Starting Dwine client {}", Dwine.VERSION);

        Dwine.modules = new ModuleManager();
        Dwine.config = new ConfigManager();
        Dwine.config.load();
        Dwine.modules.load();

        HudRenderCallback.EVENT.register((context, tickCounter) -> {
            MinecraftClient mc = MinecraftClient.getInstance();
            if (mc.player == null || mc.world == null) {
                return;
            }
            if (mc.options.hudHidden) {
                return;
            }
            Dwine.modules.renderHud(context);
        });

        ClientTickEvents.END_CLIENT_TICK.register(this::onEndTick);

        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            if (Dwine.config != null) {
                Dwine.config.save();
            }
        }, "dwine-config-save"));
    }

    private void onEndTick(MinecraftClient mc) {
        if (mc.world != null && mc.player != null) {
            Dwine.modules.onTick();
        }
        handleKeys(mc);
    }

    private void handleKeys(MinecraftClient mc) {
        if (mc.getWindow() == null) {
            return;
        }
        long handle = mc.getWindow().getHandle();
        ConfigManager config = Dwine.config;

        // Only react to bindings when no screen is capturing input (typing, menus).
        boolean canBind = mc.currentScreen == null;

        if (canBind) {
            if (pressedThisTick(handle, config.clickGuiKey)) {
                mc.setScreen(new MenuScreen());
            } else if (pressedThisTick(handle, config.hudEditorKey)) {
                mc.setScreen(new HudEditorScreen());
            } else {
                for (Module module : Dwine.modules.getModules()) {
                    int key = module.getKeyCode();
                    if (!module.isHoldKey() && key != GLFW.GLFW_KEY_UNKNOWN && pressedThisTick(handle, key)) {
                        module.toggle();
                    }
                }
            }
        }

        refreshHeld(handle);
    }

    /** Rising-edge detection: true only on the tick a key transitions to down. */
    private boolean pressedThisTick(long handle, int key) {
        if (key == GLFW.GLFW_KEY_UNKNOWN) {
            return false;
        }
        boolean down = InputUtil.isKeyPressed(handle, key);
        return down && !heldLastTick.contains(key);
    }

    private void refreshHeld(long handle) {
        heldLastTick.clear();
        for (int key : trackedKeys()) {
            if (key != GLFW.GLFW_KEY_UNKNOWN && InputUtil.isKeyPressed(handle, key)) {
                heldLastTick.add(key);
            }
        }
    }

    private Set<Integer> trackedKeys() {
        Set<Integer> keys = new HashSet<>();
        keys.add(Dwine.config.clickGuiKey);
        keys.add(Dwine.config.hudEditorKey);
        for (Module module : Dwine.modules.getModules()) {
            keys.add(module.getKeyCode());
        }
        return keys;
    }
}
