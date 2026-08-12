package com.dwine.module.impl.movement;

import com.dwine.module.Category;
import com.dwine.module.Module;

/** Keep sprinting without holding the sprint key. */
public class ToggleSprint extends Module {
    public ToggleSprint() {
        super("Toggle Sprint", "Keep sprinting without holding the key.", Category.MOVEMENT);
    }

    @Override
    public void onTick() {
        if (mc.options != null && mc.player != null && !mc.player.isUsingItem()) {
            mc.options.keySprint.setDown(true);
        }
    }

    @Override
    protected void onDisable() {
        if (mc.options != null) {
            mc.options.keySprint.setDown(false);
        }
    }
}
