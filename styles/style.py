import os

DEFAULT_PRIMARY_COLOR = "#3498db"
STYLE_DIR = os.path.dirname(__file__)

def load_styles(primary_color=None, theme="light"):
    color = primary_color or DEFAULT_PRIMARY_COLOR
    qss_path = os.path.join(STYLE_DIR, f"style_{theme}.qss")
    with open(qss_path, "r", encoding="utf-8") as f:
        qss = f.read()
    return qss.replace("$PRIMARY_COLOR", color)
