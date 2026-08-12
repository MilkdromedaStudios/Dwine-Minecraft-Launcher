package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.ItemStack;

/** Equipped armour with durability, helmet-first. */
public class ArmorHud extends HudModule {
    private static final int STEP = 18;
    private static final EquipmentSlot[] SLOTS = {
        EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET
    };

    public ArmorHud() {
        super("Armor", "Show your equipped armour and durability.", 4, 150);
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        if (mc.player == null) {
            return;
        }
        setSize(4 * STEP - 2, 16);
        int slot = 0;
        for (EquipmentSlot eq : SLOTS) {
            ItemStack stack = mc.player.getItemBySlot(eq);
            int x = slot * STEP;
            if (!stack.isEmpty()) {
                ctx.renderItem(stack, x, 0);
                ctx.renderItemDecorations(mc.font, stack, x, 0);
            }
            slot++;
        }
    }
}
