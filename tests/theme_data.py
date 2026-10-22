import json
from pathlib import Path

from deepwick_spec.color import normalize_hex

REPO = Path(__file__).resolve().parents[1]
THEME = REPO / "themes/deepwick.json"


def load_theme() -> dict:
    return json.loads(THEME.read_text())


def resolve(role: str) -> str:
    theme = load_theme()
    section, key = ("export", role.removeprefix("export.")) if role.startswith("export.") else ("colors", role)
    return normalize_hex(theme["vars"][theme[section][key]])
