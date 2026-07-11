package com.dwine.module.impl.render;

import com.dwine.module.Category;
import com.dwine.module.Module;

/** Disable the view-bobbing camera sway. */
public class NoBobbing extends Module {
    private Boolean previous;

    public NoBobbing() {
        super("No Bobbing", "Disable the view-bobbing camera sway.", Category.RENDER);
    }

    @Override
    protected void onEnable() {
        if (mc.options != null) {
            previous = mc.options.bobView().get();
            mc.options.bobView().set(false);
        }
    }

    @Override
    protected void onDisable() {
        if (mc.options != null && previous != null) {
            mc.options.bobView().set(previous);
        }
    }
}
