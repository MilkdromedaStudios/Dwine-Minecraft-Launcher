"""Theme → Qt stylesheet compiler for the launcher UI."""

from __future__ import annotations

from .themes import Theme


def _alpha(hex_color: str, alpha: float) -> str:
    """#RRGGBB -> rgba(...) with the given opacity."""
    color = hex_color.lstrip("#")[:6]
    r, g, b = (int(color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {int(alpha * 255)})"


def build_qss(theme: Theme) -> str:
    c = theme.colors
    radius = int(theme.get("radius", 10))
    font = theme.get("font", "sans-serif")
    glass = bool(theme.get("glass", False))
    surface = (
        _alpha(c["surface"], float(theme.get("glass_opacity", 0.82)))
        if glass
        else c["surface"]
    )
    return f"""
* {{
    font-family: {font};
    color: {c['text']};
    selection-background-color: {c['accent']};
    selection-color: {c['accent_text']};
    outline: none;
}}
QMainWindow, QDialog {{ background-color: {c['bg']}; }}

/* ---- navigation sidebar ---- */
#Sidebar {{
    background-color: {c['bg_alt']};
    border-right: 1px solid {c['border']};
}}
#Sidebar QPushButton {{
    background: transparent;
    border: none;
    border-radius: {radius}px;
    padding: 10px 16px;
    text-align: left;
    color: {c['text_dim']};
    font-size: 14px;
}}
#Sidebar QPushButton:hover {{ background: {c['surface']}; color: {c['text']}; }}
#Sidebar QPushButton:checked {{
    background: {_alpha(c['accent'], 0.16)};
    color: {c['accent']};
    font-weight: 600;
}}
#Logo {{ font-size: 22px; font-weight: 800; color: {c['text']}; padding: 18px 16px; }}

/* ---- cards & panels ---- */
#Card, QGroupBox {{
    background-color: {surface};
    border: 1px solid {c['border']};
    border-radius: {radius + 2}px;
}}
#CardTitle {{ font-size: 16px; font-weight: 700; }}
#Muted {{ color: {c['text_dim']}; }}

/* ---- buttons ---- */
QPushButton {{
    background-color: {c['surface_alt']};
    border: 1px solid {c['border']};
    border-radius: {radius}px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: {c['surface']}; border-color: {c['accent']}; }}
QPushButton:pressed {{ background-color: {c['bg_alt']}; }}
QPushButton:disabled {{ color: {c['text_dim']}; border-color: {c['border']}; }}
QPushButton#Primary {{
    background-color: {c['accent']};
    border: none;
    color: {c['accent_text']};
    padding: 10px 26px;
    font-size: 14px;
}}
QPushButton#Primary:hover {{ background-color: {c['accent_hover']}; }}
QPushButton#Danger {{ background-color: {c['danger']}; border: none; color: white; }}
QPushButton#Play {{
    background-color: {c['accent']};
    border: none;
    color: {c['accent_text']};
    border-radius: {radius + 6}px;
    padding: 14px 44px;
    font-size: 18px;
    font-weight: 800;
    letter-spacing: 1px;
}}
QPushButton#Play:hover {{ background-color: {c['accent_hover']}; }}

/* ---- inputs ---- */
QLineEdit, QComboBox, QSpinBox, QTextEdit, QPlainTextEdit {{
    background-color: {c['bg_alt']};
    border: 1px solid {c['border']};
    border-radius: {radius - 2}px;
    padding: 7px 10px;
}}
QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{ border-color: {c['accent']}; }}
QComboBox::drop-down {{ border: none; width: 26px; }}
QComboBox QAbstractItemView {{
    background-color: {c['surface']};
    border: 1px solid {c['border']};
    border-radius: {radius - 2}px;
}}

/* ---- sliders ---- */
QSlider::groove:horizontal {{
    height: 5px; border-radius: 2px; background: {c['surface_alt']};
}}
QSlider::sub-page:horizontal {{ background: {c['accent']}; border-radius: 2px; }}
QSlider::handle:horizontal {{
    width: 16px; height: 16px; margin: -6px 0;
    border-radius: 8px; background: {c['accent']};
}}
QSlider::handle:horizontal:hover {{ background: {c['accent_hover']}; }}

/* ---- checkbox / toggle-ish ---- */
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 5px;
    border: 1px solid {c['border']}; background: {c['bg_alt']};
}}
QCheckBox::indicator:checked {{
    background: {c['accent']}; border-color: {c['accent']};
}}

/* ---- lists / tables / scrollbars ---- */
QListWidget, QTreeWidget, QTableWidget {{
    background-color: {surface};
    border: 1px solid {c['border']};
    border-radius: {radius}px;
    padding: 4px;
}}
QListWidget::item {{ padding: 8px; border-radius: {radius - 4}px; }}
QListWidget::item:hover {{ background: {c['surface_alt']}; }}
QListWidget::item:selected {{
    background: {_alpha(c['accent'], 0.18)}; color: {c['text']};
}}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{
    background: {c['surface_alt']}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {c['text_dim']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}

/* ---- scroll areas (keep the theme background) ---- */
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QAbstractScrollArea::corner {{ background: transparent; }}

/* ---- tabs / progress / tooltips ---- */
QTabBar::tab {{
    background: transparent; color: {c['text_dim']};
    padding: 8px 16px; border-bottom: 2px solid transparent;
}}
QTabBar::tab:selected {{ color: {c['accent']}; border-bottom-color: {c['accent']}; }}
QProgressBar {{
    background: {c['surface_alt']}; border: none; border-radius: 4px;
    height: 8px; text-align: center; color: transparent;
}}
QProgressBar::chunk {{ background: {c['accent']}; border-radius: 4px; }}
QToolTip {{
    background-color: {c['surface']};
    color: {c['text']};
    border: 1px solid {c['border']};
    padding: 6px 8px;
}}
"""


def background_css(theme: Theme) -> str:
    """CSS gradient for the main window background widget."""
    bg = theme.get("background", {})
    if bg.get("type") == "solid":
        return f"background-color: {bg.get('from', theme.color('bg'))};"
    start = bg.get("from", theme.color("bg"))
    end = bg.get("to", theme.color("bg_alt"))
    return (
        "background: qlineargradient(x1:0, y1:0, x2:1, y2:1, "
        f"stop:0 {start}, stop:1 {end});"
    )
