package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.DrawContext;
import net.minecraft.item.ItemStack;

/** Equipped armour with durability, helmet-first. */
public class ArmorHud extends HudModule {
    private static final int STEP = 18;

    public ArmorHud() {
        super("Armor", "Show your equipped armour and durability.", 4, 150);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        if (mc.player == null) {
            return;
        }
        setSize(4 * STEP - 2, 16);
        int slot = 0;
        // armor is ordered feet..head; render head first.
        for (int i = mc.player.getInventory().armor.size() - 1; i >= 0; i--) {
            ItemStack stack = mc.player.getInventory().armor.get(i);
            int x = slot * STEP;
            if (!stack.isEmpty()) {
                ctx.drawItem(stack, x, 0);
                ctx.drawItemInSlot(mc.textRenderer, stack, x, 0);
            }
            slot++;
        }
    }
}
