package com.dwine.module.impl.hud;

import com.dwine.module.HudModule;
import com.dwine.setting.ModeSetting;
import net.minecraft.client.gui.GuiGraphics;

import java.text.SimpleDateFormat;
import java.util.Date;

/** Real-world clock. */
public class ClockHud extends HudModule {
    private final ModeSetting format = add(new ModeSetting("Format", "Clock format", "24 hour", "24 hour", "12 hour"));

    public ClockHud() {
        super("Clock", "Show the real-world time.", 4, 66);
    }

    @Override
    protected void renderHud(GuiGraphics ctx) {
        String pattern = format.is("12 hour") ? "hh:mm:ss a" : "HH:mm:ss";
        String label = new SimpleDateFormat(pattern).format(new Date());
        panel(ctx, mc.font.width(label), fontHeight());
        text(ctx, label, 0, 0);
    }
}
