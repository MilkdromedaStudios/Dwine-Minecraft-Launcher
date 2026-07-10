package com.dwine.setting;

import com.google.gson.JsonElement;
import com.google.gson.JsonPrimitive;

/** An ARGB colour, stored as an integer. */
public class ColorSetting extends Setting {
    private int argb;

    public ColorSetting(String name, String description, int argb) {
        super(name, description);
        this.argb = argb;
    }

    public int get() {
        return argb;
    }

    public void set(int argb) {
        this.argb = argb;
    }

    public int getRed() {
        return (argb >> 16) & 0xFF;
    }

    public int getGreen() {
        return (argb >> 8) & 0xFF;
    }

    public int getBlue() {
        return argb & 0xFF;
    }

    public int getAlpha() {
        return (argb >> 24) & 0xFF;
    }

    public void setComponents(int a, int r, int g, int b) {
        this.argb = ((a & 0xFF) << 24) | ((r & 0xFF) << 16) | ((g & 0xFF) << 8) | (b & 0xFF);
    }

    @Override
    public JsonElement write() {
        return new JsonPrimitive(argb);
    }

    @Override
    public void read(JsonElement element) {
        try {
            this.argb = element.getAsInt();
        } catch (RuntimeException ignored) {
        }
    }
}
