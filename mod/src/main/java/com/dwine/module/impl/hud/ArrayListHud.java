package com.dwine.module.impl.hud;

import com.dwine.Dwine;
import com.dwine.gui.Theme;
import com.dwine.module.Category;
import com.dwine.module.HudModule;
import com.dwine.module.Module;
import net.minecraft.client.gui.DrawContext;

import java.util.ArrayList;
import java.util.List;

/** A right-aligned list of active (non-HUD) modules — the classic "arraylist". */
public class ArrayListHud extends HudModule {
    public ArrayListHud() {
        super("Active List", "List active modules in the corner.", 320, 4);
    }

    @Override
    protected void renderHud(DrawContext ctx) {
        List<Module> active = new ArrayList<>();
        for (Module module : Dwine.modules.getModules()) {
            if (module == this || module.getCategory() == Category.HUD) {
                continue;
            }
            if (module.isEnabled()) {
                active.add(module);
            }
        }
        active.sort((a, b) -> mc.textRenderer.getWidth(b.getName()) - mc.textRenderer.getWidth(a.getName()));

        if (active.isEmpty()) {
            setSize(mc.textRenderer.getWidth("Active List"), fontHeight());
            return;
        }

        int maxWidth = 0;
        for (Module module : active) {
            maxWidth = Math.max(maxWidth, mc.textRenderer.getWidth(module.getName()));
        }
        int lineHeight = fontHeight() + 2;
        setSize(maxWidth + 3, active.size() * lineHeight);

        int y = 0;
        for (int i = 0; i < active.size(); i++) {
            Module module = active.get(i);
            int w = mc.textRenderer.getWidth(module.getName());
            int x = maxWidth - w;
            float t = active.size() <= 1 ? 0f : (float) i / (active.size() - 1);
            int accent = Theme.mix(Theme.accent, 0xFFB18CFF, t);

            ctx.fill(x - 3, y, maxWidth + 2, y + lineHeight, Theme.HUD_BG);
            ctx.fill(maxWidth + 2, y, maxWidth + 3, y + lineHeight, accent);
            ctx.drawText(mc.textRenderer, module.getName(), x, y + 1, Theme.TEXT, shadow.get());
            y += lineHeight;
        }
    }
}
