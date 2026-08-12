package com.dwine.module.impl.render;

import com.dwine.module.Category;
import com.dwine.module.Module;

/** Raise the world brightness to the maximum vanilla level. Purely visual. */
public class Fullbright extends Module {
    private Double previousGamma;

    public Fullbright() {
        super("Fullbright", "Brighten the world to the maximum vanilla level.", Category.RENDER);
    }

    @Override
    protected void onEnable() {
        if (mc.options != null) {
            previousGamma = mc.options.gamma().get();
        }
    }

    @Override
    public void onTick() {
        if (mc.options != null) {
            mc.options.gamma().set(1.0);
        }
    }

    @Override
    protected void onDisable() {
        if (mc.options != null && previousGamma != null) {
            mc.options.gamma().set(previousGamma);
        }
    }
}
