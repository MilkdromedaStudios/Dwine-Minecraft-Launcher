package com.dwine.module.impl.misc;

import com.dwine.module.Category;
import com.dwine.module.Module;
import com.dwine.setting.NumberSetting;

/** Cap the framerate while enabled — handy on laptops to save battery. */
public class FrameLimit extends Module {
    private final NumberSetting maxFps = add(new NumberSetting("Max FPS", "Frame cap while enabled", 60, 10, 260, 5));
    private Integer previous;

    public FrameLimit() {
        super("Frame Limit", "Cap your framerate to save power.", Category.MISC);
    }

    @Override
    protected void onEnable() {
        if (mc.options != null) {
            previous = mc.options.framerateLimit().get();
        }
    }

    @Override
    public void onTick() {
        if (mc.options != null) {
            mc.options.framerateLimit().set(maxFps.getInt());
        }
    }

    @Override
    protected void onDisable() {
        if (mc.options != null && previous != null) {
            mc.options.framerateLimit().set(previous);
        }
    }
}
