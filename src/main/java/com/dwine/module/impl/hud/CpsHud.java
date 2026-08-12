package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import net.minecraft.client.gui.GuiGraphics;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayDeque;
import java.util.Deque;

/** Left/right clicks per second, sampled from the raw mouse buttons. */
public class CpsHud extends HudModule {
    private final Deque<Long> leftClicks = new ArrayDeque<>();
    private final Deque<Long> rightClicks = new ArrayDeque<>();
    private boolean leftDown;
    private boolean rightDown;

    public CpsHud() {
        super("CPS", "Show clicks per second.", 4, 114);
    }

    @Override
    public void onTick() {
        if (mc.getWindow() == null) {
            return;
        }
        long handle = mc.getWindow().getWindow();
        boolean left = GLFW.glfwGetMouseButton(handle, GLFW.GLFW_MOUSE_BUTTON_LEFT) == GLFW.GLFW_PRESS;
        boolean right = GLFW.glfwGetMouseButton(handle, GLFW.GLFW_MOUSE_BUTTON_RIGHT) == GLFW.GLFW_PRESS;
        long now = System.currentTimeMillis();
        if (left && !leftDown) {
            leftClicks.add(now);
        }
        if (right && !rightDown) {
            rightClicks.add(now);
        }
        leftDown = left;
        rightDown = right;
        prune(leftClicks, now);
        prune(rightClicks, now);
    }

    private static void prune(Deque<Long> clicks, long now) {
        while (!clicks.isEmpty() && now - clicks.peekFirst() > 1000L) {
            clicks.pollFirst();
        }
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        String label = "CPS " + leftClicks.size() + " | " + rightClicks.size();
        panel(ctx, mc.font.width(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
