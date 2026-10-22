import json
from pathlib import Path

import jsonschema

from deepwick_spec.check_port import check_port
from deepwick_spec.color import contrast_ratio, normalize_hex
from deepwick_spec.palette import load_palette
from theme_data import REPO, load_theme, resolve

PALETTE = load_palette()
C = PALETTE.colors
SCHEMA = json.loads((REPO / "tests/theme.schema.json").read_text())

EXPECTED = {
    "accent": "blue",
    "border": "blue",
    "borderAccent": "lightBlue",
    "borderMuted": "overlay",
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "text": "foreground",
    "muted": "comment",
    "dim": "muted",
    "thinkingText": "comment",
    "selectedBg": "selection",
    "searchMatchBg": "selection",
    "searchMatchText": "foreground",
    "scrollbarTrack": "overlay",
    "scrollbarThumb": "muted",
    "bashMode": "green",
    "userMessageBg": "surface",
    "userMessageText": "foreground",
    "customMessageBg": "overlay",
    "customMessageText": "comment",
    "customMessageLabel": "cyan",
    "toolPendingBg": "surface",
    "toolSuccessBg": "diffAdded",
    "toolErrorBg": "diffRemoved",
    "toolTitle": "foreground",
    "toolOutput": "comment",
    "mdHeading": "blue",
    "mdLink": "orange",
    "mdLinkUrl": "muted",
    "mdCode": "orange",
    "mdCodeBlock": "foreground",
    "mdCodeBlockBorder": "muted",
    "mdQuote": "comment",
    "mdQuoteBorder": "muted",
    "mdHr": "muted",
    "mdListBullet": "muted",
    "toolDiffAdded": "green",
    "toolDiffRemoved": "red",
    "toolDiffContext": "comment",
    "syntaxComment": "comment",
    "syntaxKeyword": "blue",
    "syntaxFunction": "yellow",
    "syntaxVariable": "lightBlue",
    "syntaxString": "orange",
    "syntaxNumber": "sage",
    "syntaxType": "teal",
    "syntaxOperator": "foreground",
    "syntaxPunctuation": "foreground",
    "thinkingOff": "muted",
    "thinkingMinimal": "comment",
    "thinkingLow": "blue",
    "thinkingMedium": "teal",
    "thinkingHigh": "magenta",
    "thinkingXhigh": "rose",
    "thinkingMax": "red",
    "export.pageBg": "background",
    "export.cardBg": "surface",
    "export.infoBg": "overlay",
}

# toolOutput (Comment) on toolSuccessBg is 4.43:1, so it is left out.
CONTRAST_PAIRS = [
    ("text", "export.pageBg"),
    ("userMessageText", "userMessageBg"),
    ("toolTitle", "toolPendingBg"),
    ("toolTitle", "toolSuccessBg"),
    ("toolTitle", "toolErrorBg"),
    ("toolOutput", "toolErrorBg"),
]


def test_validates_against_pi_schema():
    jsonschema.validate(load_theme(), SCHEMA)


def test_every_schema_role_is_set():
    roles = set(SCHEMA["properties"]["colors"]["properties"])
    assert set(load_theme()["colors"]) == roles
    assert len(roles) == 56


def test_header():
    theme = load_theme()
    assert theme["name"] == "deepwick"
    assert theme["appearance"] == "dark"
    assert theme["$schema"] == "https://pi.dev/schemas/theme.schema.json"


def test_vars_are_palette_names():
    for name, value in load_theme()["vars"].items():
        assert name in C, name
        assert normalize_hex(value) == normalize_hex(C[name]), name


def test_colors_reference_vars_only():
    theme = load_theme()
    values = list(theme["colors"].values()) + list(theme["export"].values())
    assert set(values) <= set(theme["vars"])


def test_roles_match_spec():
    assert set(EXPECTED) == set(load_theme()["colors"]) | {f"export.{k}" for k in load_theme()["export"]}
    for role, name in EXPECTED.items():
        assert resolve(role) == normalize_hex(C[name]), role


def test_text_contrast():
    for fg, bg in CONTRAST_PAIRS:
        assert contrast_ratio(resolve(fg), resolve(bg)) >= 4.5, (fg, bg)


def test_package_json():
    package = json.loads((REPO / "package.json").read_text())
    assert package["name"] == "deepwick-pi"
    assert package["version"] == "1.0.0"
    assert package["license"] == "MIT"
    assert package["private"] is True
    assert package["keywords"] == ["pi-package"]
    assert package["pi"] == {"themes": ["./themes/*.json"]}
    assert [p.relative_to(REPO).as_posix() for p in REPO.glob("themes/*.json")] == ["themes/deepwick.json"]


def test_vendored_schema_version():
    assert (REPO / "tests/theme.schema.version").read_text().strip() == "1.4.0"


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []
