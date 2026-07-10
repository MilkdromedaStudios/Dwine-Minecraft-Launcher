package com.dwine.setting;

import com.google.gson.JsonElement;

/**
 * Base type for a module setting. Every setting knows how to serialise
 * itself to (and read itself from) the shared {@code features.json} that the
 * Dwine launcher and this mod both understand.
 */
public abstract class Setting {
    private final String name;
    private final String description;

    protected Setting(String name, String description) {
        this.name = name;
        this.description = description;
    }

    public String getName() {
        return name;
    }

    public String getDescription() {
        return description;
    }

    /** Serialise the current value for storage in features.json. */
    public abstract JsonElement write();

    /** Load a previously stored value. Unknown/garbage values are ignored. */
    public abstract void read(JsonElement element);
}
