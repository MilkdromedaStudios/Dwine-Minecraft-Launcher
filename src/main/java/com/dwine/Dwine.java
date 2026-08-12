package com.dwine;

import com.dwine.config.ConfigManager;
import com.dwine.module.ModuleManager;

/** Shared, statically-accessible handles to Dwine's subsystems. */
public final class Dwine {
    private Dwine() {
    }

    public static final String NAME = "Dwine";
    public static final String VERSION = "0.1.0";

    public static ModuleManager modules;
    public static ConfigManager config;
}
