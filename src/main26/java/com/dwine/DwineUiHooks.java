package com.dwine;

import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.Screens;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.network.chat.Component;

/** Adds the branded Dwine client shell to vanilla title and pause screens. */
public final class DwineUiHooks {
    private DwineUiHooks() { }

    public static void register() {
        ScreenEvents.AFTER_INIT.register((client, screen, scaledWidth, scaledHeight) -> {
            if (screen instanceof TitleScreen || screen instanceof PauseScreen) {
                int x = scaledWidth - 126;
                int y = screen instanceof TitleScreen ? 12 : scaledHeight - 34;
                Screens.getWidgets(screen).add(Button.builder(
                                Component.literal("Dwine Client"),
                                button -> client.gui.setScreen(new DwineScreen(Component.literal("Dwine"))))
                        .bounds(x, y, 114, 22)
                        .build());
            }

            if (screen instanceof TitleScreen) {
                ScreenEvents.afterBackground(screen).register((s, graphics, mouseX, mouseY, tickProgress) -> {
                    // Cover the vanilla panorama with Dwine's dark indigo client backdrop.
                    graphics.fill(0, 0, 10000, 10000, 0xFF080B16);
                    graphics.fill(0, 0, 10000, 92, 0xFF111633);
                    graphics.fill(0, 92, 10000, 188, 0xFF171A3B);
                    graphics.fill(0, 188, 10000, 10000, 0xFF0C1020);
                    graphics.text(client.font, "DWINE", 22, 20, 0xFFB19CFF, true);
                    graphics.text(client.font, "Minecraft 26.2 Client", 22, 38, 0xFFFFFFFF, true);
                    graphics.text(client.font, "A cleaner client experience • modules • HUD • movement • render", 22, 56, 0xFF98A2C8, true);
                    graphics.text(client.font, "RShift / J  Open Dwine", 22, 76, 0xFF7D88AF, true);
                });
            }
        });
    }
}
