from dwine.theme.engine import background_css, build_qss
from dwine.theme.themes import BUILTIN, list_themes, load_theme


def test_builtin_themes_load():
    for name in BUILTIN:
        theme = load_theme(name)
        assert theme.color("accent").startswith("#")
        assert theme.color("bg").startswith("#")


def test_theme_list_contains_required_styles():
    themes = list_themes()
    for required in ("dwine-dark", "dwine-light", "neon", "minimal", "glass"):
        assert required in themes


def test_qss_generation():
    for name in BUILTIN:
        theme = load_theme(name)
        qss = build_qss(theme)
        assert "QPushButton#Play" in qss
        assert theme.color("accent") in qss
        assert background_css(theme)


def test_unknown_theme_falls_back():
    theme = load_theme("does-not-exist")
    assert theme.name == "dwine-dark"
