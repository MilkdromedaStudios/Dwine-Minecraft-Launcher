package com.dwine.setting;

import com.google.gson.JsonElement;
import com.google.gson.JsonPrimitive;

/** A double-valued slider with a min, max and step. */
public class NumberSetting extends Setting {
    private double value;
    private final double min;
    private final double max;
    private final double step;

    public NumberSetting(String name, String description, double value, double min, double max, double step) {
        super(name, description);
        this.min = min;
        this.max = max;
        this.step = step;
        this.value = clamp(value);
    }

    public double get() {
        return value;
    }

    public int getInt() {
        return (int) Math.round(value);
    }

    public float getFloat() {
        return (float) value;
    }

    public void set(double value) {
        this.value = clamp(value);
    }

    /** Set from a 0..1 slider fraction. */
    public void setFraction(double fraction) {
        double raw = min + (max - min) * Math.max(0.0, Math.min(1.0, fraction));
        set(Math.round(raw / step) * step);
    }

    public double getFraction() {
        if (max == min) {
            return 0.0;
        }
        return (value - min) / (max - min);
    }

    public double getMin() {
        return min;
    }

    public double getMax() {
        return max;
    }

    private double clamp(double v) {
        return Math.max(min, Math.min(max, v));
    }

    @Override
    public JsonElement write() {
        return new JsonPrimitive(value);
    }

    @Override
    public void read(JsonElement element) {
        try {
            set(element.getAsDouble());
        } catch (RuntimeException ignored) {
        }
    }
}
