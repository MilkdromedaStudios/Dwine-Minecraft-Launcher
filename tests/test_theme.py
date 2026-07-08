import zipfile

from dwine.features.crosshair import PRESETS, Crosshair
from dwine.theme.engine import background_css, build_qss
from dwine.theme.mcpack import build_pack, enable_in_options, pack_format_for
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


def test_pack_format_table():
    assert pack_format_for("1.8.9") == 1
    assert pack_format_for("1.12.2") == 3
    assert pack_format_for("1.16.5") == 6
    assert pack_format_for("1.20.1") == 15
    assert pack_format_for("1.20.4") == 22
    assert pack_format_for("1.21") == 34
    assert pack_format_for("24w14a") == 34  # snapshot: assume modern


def test_resource_pack_generation(tmp_path):
    theme = load_theme("neon")
    pack = build_pack(theme, "1.21", tmp_path, Crosshair(shape="plus_dot"))
    assert pack.exists()
    with zipfile.ZipFile(pack) as zf:
        names = zf.namelist()
        assert "pack.mcmeta" in names
        assert "assets/minecraft/textures/gui/widgets.png" in names
        assert "assets/minecraft/textures/gui/sprites/widget/button.png" in names
        assert "assets/minecraft/textures/gui/sprites/hud/crosshair.png" in names
        assert "assets/minecraft/textures/gui/sprites/widget/button.png.mcmeta" in names


def test_enable_in_options(tmp_path):
    enable_in_options(tmp_path)
    text = (tmp_path / "options.txt").read_text()
    assert '"file/Dwine Theme.zip"' in text
    # idempotent
    enable_in_options(tmp_path)
    text = (tmp_path / "options.txt").read_text()
    assert text.count("Dwine Theme.zip") == 1
    # merges into an existing options.txt without clobbering other lines
    (tmp_path / "options.txt").write_text(
        'fov:0.5\nresourcePacks:["vanilla"]\n', encoding="utf-8"
    )
    enable_in_options(tmp_path)
    text = (tmp_path / "options.txt").read_text()
    assert "fov:0.5" in text and '"vanilla"' in text and "Dwine Theme.zip" in text


def test_crosshair_presets_render():
    for name, crosshair in PRESETS.items():
        image = crosshair.render()
        assert image.size == (crosshair.size, crosshair.size), name
