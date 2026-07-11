package com.dwine.module;

import com.dwine.module.impl.hud.ArmorHud;
import com.dwine.module.impl.hud.BiomeHud;
import com.dwine.module.impl.hud.ClockHud;
import com.dwine.module.impl.hud.CoordinatesHud;
import com.dwine.module.impl.hud.CpsHud;
import com.dwine.module.impl.hud.DirectionHud;
import com.dwine.module.impl.hud.FpsHud;
import com.dwine.module.impl.hud.KeystrokesHud;
import com.dwine.module.impl.hud.PingHud;
import com.dwine.module.impl.hud.PotionHud;
import com.dwine.module.impl.hud.SessionHud;
import com.dwine.module.impl.hud.SpeedHud;
import com.dwine.module.impl.hud.WatermarkHud;
import com.dwine.module.impl.misc.FrameLimit;
import com.dwine.module.impl.movement.AutoSprint;
import com.dwine.module.impl.movement.ToggleSneak;
import com.dwine.module.impl.movement.ToggleSprint;
import com.dwine.module.impl.render.FovChanger;
import com.dwine.module.impl.render.Fullbright;
import com.dwine.module.impl.render.NoBobbing;
import com.dwine.module.impl.render.Zoom;
import net.minecraft.client.gui.GuiGraphics;
import org.lwjgl.glfw.GLFW;

import java.util.ArrayList;
import java.util.List;

/** Owns every module, dispatches ticks/HUD rendering, and resolves toggles. */
public class ModuleManager {
    private final List<Module> modules = new ArrayList<>();

    public ModuleManager() {
        // HUD
        register(new WatermarkHud());
        register(new FpsHud());
        register(new CpsHud());
        register(new CoordinatesHud());
        register(new DirectionHud());
        register(new PingHud());
        register(new ClockHud());
        register(new KeystrokesHud());
        register(new ArmorHud());
        register(new PotionHud());
        register(new SessionHud());
        register(new SpeedHud());
        register(new BiomeHud());

        // Render
        register(new Fullbright());
        register(new Zoom());
        register(new NoBobbing());
        register(new FovChanger());

        // Movement
        register(new ToggleSprint());
        register(new ToggleSneak());
        register(new AutoSprint());

        // Misc
        register(new FrameLimit());
    }

    private void register(Module module) {
        modules.add(module);
    }

    public List<Module> getModules() {
        return modules;
    }

    public List<Module> getByCategory(Category category) {
        List<Module> out = new ArrayList<>();
        for (Module module : modules) {
            if (module.getCategory() == category) {
                out.add(module);
            }
        }
        return out;
    }

    public Module getByName(String name) {
        for (Module module : modules) {
            if (module.getName().equalsIgnoreCase(name)) {
                return module;
            }
        }
        return null;
    }

    public List<HudModule> getHudModules() {
        List<HudModule> out = new ArrayList<>();
        for (Module module : modules) {
            if (module instanceof HudModule hud) {
                out.add(hud);
            }
        }
        return out;
    }

    /** Fire onLoad for every module once config has been applied. */
    public void load() {
        for (Module module : modules) {
            module.onLoad();
        }
    }

    public void onTick() {
        for (Module module : modules) {
            if (module.isEnabled()) {
                module.onTick();
            }
        }
    }

    public void renderHud(GuiGraphics ctx) {
        for (HudModule hud : getHudModules()) {
            if (hud.isEnabled()) {
                hud.render(ctx);
            }
        }
    }

    /** Toggle any module bound to the given key. Returns true if one matched. */
    public boolean onKeyPressed(int keyCode) {
        if (keyCode == GLFW.GLFW_KEY_UNKNOWN) {
            return false;
        }
        boolean matched = false;
        for (Module module : modules) {
            if (module.isHoldKey()) {
                continue;
            }
            if (module.getKeyCode() == keyCode) {
                module.toggle();
                matched = true;
            }
        }
        return matched;
    }
}
