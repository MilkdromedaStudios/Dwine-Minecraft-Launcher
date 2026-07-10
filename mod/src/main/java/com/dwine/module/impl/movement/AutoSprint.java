package com.dwine.module.impl.movement;

import com.dwine.module.Category;
import com.dwine.module.Module;

/** Automatically sprint whenever you move forward. */
public class AutoSprint extends Module {
    public AutoSprint() {
        super("Auto Sprint", "Automatically sprint when moving forward.", Category.MOVEMENT);
    }

    @Override
    public void onTick() {
        if (mc.options == null || mc.player == null) {
            return;
        }
        if (mc.options.forwardKey.isPressed() && !mc.player.horizontalCollision) {
            mc.options.sprintKey.setPressed(true);
        }
    }

    @Override
    protected void onDisable() {
        if (mc.options != null) {
            mc.options.sprintKey.setPressed(false);
        }
    }
}
