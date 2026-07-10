package com.dwine.module.impl.movement;

import com.dwine.module.Category;
import com.dwine.module.Module;

/** Stay sneaking without holding the sneak key. */
public class ToggleSneak extends Module {
    public ToggleSneak() {
        super("Toggle Sneak", "Stay sneaking without holding the key.", Category.MOVEMENT);
    }

    @Override
    public void onTick() {
        if (mc.options != null) {
            mc.options.sneakKey.setPressed(true);
        }
    }

    @Override
    protected void onDisable() {
        if (mc.options != null) {
            mc.options.sneakKey.setPressed(false);
        }
    }
}
