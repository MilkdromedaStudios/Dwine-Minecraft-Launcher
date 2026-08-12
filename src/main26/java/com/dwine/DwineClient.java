package com.dwine;

import com.mojang.blaze3d.platform.InputConstants;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.minecraft.client.KeyMapping;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/** Minecraft 26.2 native Dwine client entrypoint. */
public final class DwineClient implements ClientModInitializer {
    public static final String MOD_ID = "dwine";
    public static final String VERSION = "0.5.0";
    public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

    private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(
            Identifier.fromNamespaceAndPath(MOD_ID, "general"));

    private static final KeyMapping OPEN_DWINE = KeyMappingHelper.registerKeyMapping(
            new KeyMapping("key.dwine.open_menu", InputConstants.Type.KEYSYM, InputConstants.KEY_RSHIFT, CATEGORY));
    private static final KeyMapping OPEN_DWINE_FALLBACK = KeyMappingHelper.registerKeyMapping(
            new KeyMapping("key.dwine.open_menu_fallback", InputConstants.Type.KEYSYM, InputConstants.KEY_J, CATEGORY));
    private static final KeyMapping ZOOM = KeyMappingHelper.registerKeyMapping(
            new KeyMapping("key.dwine.zoom", InputConstants.Type.KEYSYM, InputConstants.KEY_C, CATEGORY));

    private boolean sprintLatched;
    private boolean sneakLatched;
    private boolean sprintWasDown;
    private boolean sneakWasDown;
    private boolean menuKeyWasDown;

    @Override
    public void onInitializeClient() {
        LOGGER.info("Starting Dwine {} for Minecraft 26.2", VERSION);
        DwineFeatures.INSTANCE.registerHud();
        DwineUiHooks.register();

        ClientTickEvents.END_CLIENT_TICK.register(client -> {
            boolean requestedMenu = OPEN_DWINE.consumeClick() || OPEN_DWINE_FALLBACK.consumeClick();
            boolean menuKeyDown = OPEN_DWINE.isDown() || OPEN_DWINE_FALLBACK.isDown();
            if (requestedMenu || (menuKeyDown && !menuKeyWasDown)) {
                client.gui.setScreen(new DwineScreen(Component.literal("Dwine")));
            }
            menuKeyWasDown = menuKeyDown;

            DwineFeatures.INSTANCE.tick(client, ZOOM.isDown());
            if (client.player == null) return;

            boolean sprintDown = client.options.keySprint.isDown();
            if (DwineFeatures.INSTANCE.enabled("Toggle Sprint")) {
                if (sprintDown && !sprintWasDown) sprintLatched = !sprintLatched;
                if (sprintLatched) client.player.setSprinting(true);
            } else {
                sprintLatched = false;
            }
            sprintWasDown = sprintDown;

            boolean sneakDown = client.options.keyShift.isDown();
            if (DwineFeatures.INSTANCE.enabled("Toggle Sneak")) {
                if (sneakDown && !sneakWasDown) sneakLatched = !sneakLatched;
                client.options.keyShift.setDown(sneakLatched || sneakDown);
            } else {
                sneakLatched = false;
            }
            sneakWasDown = sneakDown;
        });
    }
}
