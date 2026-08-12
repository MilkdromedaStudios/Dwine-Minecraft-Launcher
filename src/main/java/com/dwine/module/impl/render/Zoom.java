package com.dwine.module.impl.render;

import com.dwine.module.Category;
import com.dwine.module.Module;
import com.dwine.setting.NumberSetting;
import org.lwjgl.glfw.GLFW;

/** Hold a key to zoom in by lowering the field of view. */
public class Zoom extends Module {
    private final NumberSetting zoomFov = add(new NumberSetting("FOV", "Field of view while zooming", 30, 30, 70, 1));
    private Integer savedFov;

    public Zoom() {
        super("Zoom", "Hold a key to zoom in.", Category.RENDER);
        markHoldKey();
        setKeyCode(GLFW.GLFW_KEY_C);
        setEnabledQuiet(true);
    }

    @Override
    public void onTick() {
        if (mc.options == null) {
            return;
        }
        if (isKeyHeld()) {
            if (savedFov == null) {
                savedFov = mc.options.fov().get();
            }
            mc.options.fov().set(zoomFov.getInt());
        } else if (savedFov != null) {
            mc.options.fov().set(savedFov);
            savedFov = null;
        }
    }

    @Override
    protected void onDisable() {
        if (mc.options != null && savedFov != null) {
            mc.options.fov().set(savedFov);
            savedFov = null;
        }
    }
}
