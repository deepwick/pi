import pytest

from deepwick_spec.ansi import plain, runs
from deepwick_spec.palette import load_palette
from deepwick_spec.tui import capture
from pi_run import MODEL, agent_dir_guard, prepare, replay_command, requires_pi
from theme_data import REPO

pytestmark = requires_pi

C = {name: value.lower() for name, value in load_palette().colors.items()}
LAST_LINE = "rename it instead"
FOOTER_MODEL = "{} • {}".format(*MODEL.split("/", 1)[1].split(":"))


def replay(tmp_path, **kwargs) -> str:
    with agent_dir_guard():
        return capture(replay_command(prepare(tmp_path), **kwargs), size=(120, 140), wait_for=LAST_LINE, timeout=30, settle=1.0)


@pytest.fixture(scope="module")
def pane(tmp_path_factory):
    return replay(tmp_path_factory.mktemp("replay"))


def style(pane: str, needle: str, after: str | None = None) -> dict:
    """Style of the first run whose stripped text is `needle`, optionally after the run containing `after`."""
    found = after is None
    for text, st in runs(pane):
        if not found:
            found = after in text
            continue
        if text.strip() == needle:
            return st
    raise AssertionError(f"no run {needle!r}" + (f" after {after!r}" if after else ""))


def containing(pane: str, needle: str) -> dict:
    for text, st in runs(pane):
        if needle in text:
            return st
    raise AssertionError(f"no run contains {needle!r}")


def test_truecolor_detected(pane):
    assert any(st["fg"] == C["foreground"] for _, st in runs(pane)), "pi did not emit truecolor in tmux; check COLORTERM"


def test_theme_loads_without_errors(pane):
    text = plain(pane)
    for sentinel in ("Theme conflicts", "Invalid theme", "Failed to load theme"):
        assert sentinel not in text


def test_replay_restores_model(pane):
    text = plain(pane)
    assert "Could not restore model" not in text
    assert FOOTER_MODEL in text


def test_user_message(pane):
    st = containing(pane, "Explain what sample.py does")
    assert (st["fg"], st["bg"]) == (C["foreground"], C["surface"])


def test_markdown(pane):
    heading = containing(pane, "What ")
    assert heading["fg"] == C["blue"] and heading["bold"]
    assert style(pane, "Enum")["fg"] == C["orange"]
    assert style(pane, "enum")["fg"] == C["orange"]
    assert style(pane, "(https://docs.python.org/3/library/enum.html)")["fg"] == C["muted"]
    assert style(pane, "-", after="Key parts")["fg"] == C["muted"]
    assert containing(pane, "Deepwick sample: exercises")["fg"] == C["comment"]


def test_code_block(pane):
    block = "```python"
    assert style(pane, "# Greet each name a few times")["fg"] == C["comment"]
    assert style(pane, "class", after=block)["fg"] == C["blue"]
    assert style(pane, "Developer", after=block)["fg"] == C["yellow"]
    assert style(pane, "greet(", after=block)["fg"] == C["yellow"]
    assert style(pane, "str", after=block)["fg"] == C["teal"]
    assert style(pane, 'f"Hello,', after=block)["fg"] == C["orange"]
    assert style(pane, "3", after=block)["fg"] == C["sage"]
    assert style(pane, "self, name:", after=block)["fg"] == C["lightBlue"]


def test_tool_backgrounds(pane):
    assert containing(pane, "$ python3 --version")["bg"] == C["diffAdded"]
    assert containing(pane, "$ ls does-not-exist")["bg"] == C["diffRemoved"]
    output = style(pane, "Python 3.14.8", after="$ python3 --version")
    assert (output["fg"], output["bg"]) == (C["comment"], C["diffAdded"])


def test_diff(pane):
    assert containing(pane, "+38 def")["fg"] == C["green"]
    assert containing(pane, "-38 def")["fg"] == C["red"]
    assert containing(pane, " 39     count = 0.0")["fg"] == C["comment"]


def test_thinking_text(pane):
    assert containing(pane, "I'm trying to identify")["fg"] == C["comment"]


def test_editor_border(pane):
    borders = [st["fg"] for text, st in runs(pane) if text.strip() and set(text.strip()) == {"─"}]
    assert borders and borders[-1] == C["teal"]


def test_repo_dir_loads_as_theme_source(tmp_path):
    other = replay(tmp_path, theme_source=REPO / "themes")
    assert containing(other, "What ")["fg"] == C["blue"]
