package com.dwine;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keybinding.v1.KeyBindingHelper;
import net.minecraft.client.KeyMapping;
import net.minecraft.client.Minecraft;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Minecraft 26.2 native Dwine client entrypoint. */
public final class DwineClient implements ClientModInitializer {
    public static final String MOD_ID = "dwine";
    public static final String VERSION = "0.3.0";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(
            Identifier.fromNamespaceAndPath(MOD_ID, "general"));

    private static final KeyMapping OPEN_DWINE = KeyBindingHelper.registerKeyBinding(
            new KeyMapping(
                    "key.dwine.open_menu",
                    InputConstants.Type.KEYSYM,
                    InputConstants.KEY_J,
                    CATEGORY));

    @Override
    public void onInitializeClient() {
        LOGGER.info("Starting Dwine {} for Minecraft 26.2", VERSION);

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            while (OPEN_DWINE.consumeClick()) {
                if (client.currentScreen == null) {
                    Minecraft.getInstance().setScreen(new DwineScreen(Component.literal("Dwine")));
                }
            }
        });
    }
}
