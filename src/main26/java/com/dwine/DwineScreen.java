package com.dwine;

import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Branded, categorized Dwine 26.2 module browser. */
public final class DwineScreen extends Screen {
    private static final int PAGE_SIZE = 8;
    private final String selectedCategory;
    private final int page;

    public DwineScreen(Component title) { this(title, "HUD", 0); }

    private DwineScreen(Component title, String selectedCategory, int page) {
        super(title);
        this.selectedCategory = selectedCategory;
        this.page = Math.max(0, page);
    }

    @Override
    protected void init() {
        int panelX = this.width / 2 - 270;
        int panelY = 20;
        List<String> cats = DwineFeatures.INSTANCE.categoryNames();

        int tabW = 96;
        for (int i = 0; i < cats.size(); i++) {
            String category = cats.get(i);
            String title = category.equals(selectedCategory) ? "● " + category : category;
            this.addRenderableWidget(new DwineButton(panelX + 18 + i * 102, panelY + 62, tabW, 22,
                    Component.literal(title), b -> this.minecraft.gui.setScreen(new DwineScreen(Component.literal("Dwine"), category, 0)), true));
        }

        List<String> names = DwineFeatures.INSTANCE.namesForCategory(selectedCategory);
        int pageCount = Math.max(1, (names.size() + PAGE_SIZE - 1) / PAGE_SIZE);
        int safePage = Math.min(page, pageCount - 1);
        int from = safePage * PAGE_SIZE;
        int to = Math.min(names.size(), from + PAGE_SIZE);
        int startY = panelY + 100;

        for (int i = from; i < to; i++) {
            String name = names.get(i);
            int slot = i - from;
            int col = slot % 2;
            int row = slot / 2;
            this.addRenderableWidget(new DwineButton(panelX + 18 + col * 258, startY + row * 34, 240, 26,
                    label(name), b -> {
                        boolean enabled = DwineFeatures.INSTANCE.toggle(name);
                        b.setMessage(Component.literal(name + (enabled ? "   ON" : "   OFF")));
                    }));
        }

        int navY = panelY + 244;
        if (safePage > 0) this.addRenderableWidget(new DwineButton(panelX + 18, navY, 116, 22, Component.literal("‹ Previous"),
                b -> this.minecraft.gui.setScreen(new DwineScreen(Component.literal("Dwine"), selectedCategory, safePage - 1)), true));
        if (safePage + 1 < pageCount) this.addRenderableWidget(new DwineButton(panelX + 142, navY, 116, 22, Component.literal("Next ›"),
                b -> this.minecraft.gui.setScreen(new DwineScreen(Component.literal("Dwine"), selectedCategory, safePage + 1)), true));

        this.addRenderableWidget(new DwineButton(panelX + 282, navY, 116, 22, Component.literal("HUD Editor"),
                b -> this.minecraft.gui.setScreen(new DwineHudScreen(Component.literal("Dwine HUD"))), true));
        this.addRenderableWidget(new DwineButton(panelX + 406, navY, 116, 22, Component.literal("Done"),
                b -> this.minecraft.gui.setScreen(null), true));
    }

    private Component label(String name) {
        return Component.literal(name + (DwineFeatures.INSTANCE.enabled(name) ? "   ON" : "   OFF"));
    }

    @Override
    public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float delta) {
        int x = this.width / 2 - 270;
        int y = 20;
        graphics.fill(0, 0, 10000, 10000, 0xDF070A14);
        if (DwineFeatures.INSTANCE.enabled("Menu Glow")) graphics.fill(x - 3, y - 3, x + 543, y + 305, 0x558E7CFF);
        graphics.fill(x, y, x + 540, y + 302, 0xFA15192B);
        graphics.fill(x, y, x + 540, y + 52, 0xFF202647);
        if (DwineFeatures.INSTANCE.enabled("Menu Accent")) graphics.fill(x, y + 51, x + 540, y + 54, 0xFF8E7CFF);
        graphics.text(this.font, "DWINE", x + 18, y + 15, 0xFFB8A7FF, true);
        if (DwineFeatures.INSTANCE.enabled("Menu Version")) graphics.text(this.font, "client 0.7 • Minecraft 26.2", x + 74, y + 15, 0xFFA8B0C8, false);
        graphics.text(this.font, selectedCategory + " Modules", x + 18, y + 88, 0xFFFFFFFF, true);
        if (DwineFeatures.INSTANCE.enabled("Menu Module Count")) graphics.text(this.font, DwineFeatures.INSTANCE.count() + " total modules", x + 430, y + 88, 0xFF9AA5C7, false);
        if (DwineFeatures.INSTANCE.enabled("Menu Tips")) graphics.text(this.font, "RShift / J: menu   •   C: zoom   •   settings save automatically", x + 18, y + 282, 0xFF7783A6, false);
        super.extractRenderState(graphics, mouseX, mouseY, delta);
    }

    @Override public boolean isPauseScreen() { return false; }
}
