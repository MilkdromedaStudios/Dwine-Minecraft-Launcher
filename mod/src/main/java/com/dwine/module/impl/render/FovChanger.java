package com.dwine.module.impl.render;

import com.dwine.module.Category;
import com.dwine.module.Module;
import com.dwine.setting.NumberSetting;

/** Override your field of view to a fixed value. */
public class FovChanger extends Module {
    private final NumberSetting fov = add(new NumberSetting("FOV", "Field of view", 90, 30, 110, 1));
    private Integer previous;

    public FovChanger() {
        super("FOV Changer", "Override your field of view.", Category.RENDER);
    }

    @Override
    protected void onEnable() {
        if (mc.options != null) {
            previous = mc.options.getFov().getValue();
        }
    }

    @Override
    public void onTick() {
        if (mc.options != null) {
            mc.options.getFov().setValue(fov.getInt());
        }
    }

    @Override
    protected void onDisable() {
        if (mc.options != null && previous != null) {
            mc.options.getFov().setValue(previous);
        }
    }
}
