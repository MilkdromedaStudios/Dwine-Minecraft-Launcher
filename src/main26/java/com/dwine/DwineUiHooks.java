package com.dwine;

import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.fabric.api.client.screen.v1.Screens;
import net.minecraft.client.gui.screens.PauseScreen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.network.chat.Component;

/** Adds the branded Dwine client shell to vanilla title and pause screens. */
public final class DwineUiHooks {
    private DwineUiHooks() { }

    public static void register() {
        ScreenEvents.AFTER_INIT.register((client, screen, scaledWidth, scaledHeight) -> {
            if (screen instanceof TitleScreen || screen instanceof PauseScreen) {
                int x = scaledWidth - 138;
                int y = screen instanceof TitleScreen ? 14 : scaledHeight - 38;
                Screens.getWidgets(screen).add(new DwineButton(x, y, 124, 24,
                        Component.literal("✦ Dwine Client"),
                        button -> client.gui.setScreen(new DwineScreen(Component.literal("Dwine"))), true));
            }

            if (screen instanceof TitleScreen) {
                ScreenEvents.afterBackground(screen).register((s, graphics, mouseX, mouseY, tickProgress) -> {
                    graphics.fill(0, 0, 10000, 10000, 0xFF070A14);
                    graphics.fill(0, 0, 10000, 104, 0xFF10152D);
                    graphics.fill(0, 104, 10000, 210, 0xFF171B3A);
                    graphics.fill(0, 210, 10000, 10000, 0xFF0A0E1C);
                    graphics.fill(0, 102, 10000, 105, 0xFF8E7CFF);
                    if (DwineFeatures.INSTANCE.enabled("Title Branding")) graphics.text(client.font, "DWINE", 24, 22, 0xFFB9AAFF, true);
                    if (DwineFeatures.INSTANCE.enabled("Title Subtitle")) graphics.text(client.font, "Minecraft 26.2 Client", 24, 42, 0xFFFFFFFF, true);
                    graphics.text(client.font, "105 client-side modules • custom HUD • render • movement • utilities", 24, 62, 0xFF9CA7C9, false);
                    graphics.text(client.font, "RShift / J  Open Client     C  Zoom", 24, 82, 0xFF7783A6, false);
                    if (DwineFeatures.INSTANCE.enabled("Title Footer")) graphics.text(client.font, "Dwine Client 0.7", 24, scaledHeight - 18, 0xFF626D8E, false);
                });
            }
        });
    }
}
