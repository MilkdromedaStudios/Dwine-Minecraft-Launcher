package com.dwine.module;

/** Top-level grouping shown as a column in the ClickGUI. */
public enum Category {
    HUD("HUD"),
    RENDER("Render"),
    MOVEMENT("Movement"),
    MISC("Misc");

    private final String title;

    Category(String title) {
        this.title = title;
    }

    public String getTitle() {
        return title;
    }
}
