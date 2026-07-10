package com.dwine.setting;

import com.google.gson.JsonElement;
import com.google.gson.JsonPrimitive;

public class BooleanSetting extends Setting {
    private boolean value;

    public BooleanSetting(String name, String description, boolean value) {
        super(name, description);
        this.value = value;
    }

    public boolean get() {
        return value;
    }

    public void set(boolean value) {
        this.value = value;
    }

    public void toggle() {
        this.value = !this.value;
    }

    @Override
    public JsonElement write() {
        return new JsonPrimitive(value);
    }

    @Override
    public void read(JsonElement element) {
        try {
            this.value = element.getAsBoolean();
        } catch (RuntimeException ignored) {
        }
    }
}
