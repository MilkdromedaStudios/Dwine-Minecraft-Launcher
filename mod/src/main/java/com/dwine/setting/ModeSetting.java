package com.dwine.setting;

import com.google.gson.JsonElement;
import com.google.gson.JsonPrimitive;

import java.util.Arrays;
import java.util.List;

/** A setting that cycles through a fixed list of string options. */
public class ModeSetting extends Setting {
    private final List<String> options;
    private int index;

    public ModeSetting(String name, String description, String value, String... options) {
        super(name, description);
        this.options = Arrays.asList(options);
        this.index = Math.max(0, this.options.indexOf(value));
    }

    public String get() {
        return options.get(index);
    }

    public boolean is(String option) {
        return get().equalsIgnoreCase(option);
    }

    public List<String> getOptions() {
        return options;
    }

    public void cycle() {
        index = (index + 1) % options.size();
    }

    public void cycleBack() {
        index = (index - 1 + options.size()) % options.size();
    }

    public void set(String value) {
        int i = options.indexOf(value);
        if (i >= 0) {
            index = i;
        }
    }

    @Override
    public JsonElement write() {
        return new JsonPrimitive(get());
    }

    @Override
    public void read(JsonElement element) {
        try {
            set(element.getAsString());
        } catch (RuntimeException ignored) {
        }
    }
}
