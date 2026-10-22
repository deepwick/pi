import json
import shlex
import shutil
from contextlib import contextmanager
from pathlib import Path

import pytest

from deepwick_spec.tui import tmux_available
from theme_data import REPO, THEME

FIXTURES = REPO / "tests/fixtures"
FIXTURE_CWD = "/home/user/project"
MODEL = "github-copilot/claude-haiku-5.5:medium"
REPLAY_FLAGS = ("--offline", "-ne", "-ns", "-np", "-nc", "--no-mcp")
AGENT_DIR = Path.home() / ".pi/agent"

requires_pi = pytest.mark.skipif(not (shutil.which("pi") and tmux_available()), reason="requires pi and tmux")


def prepare(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    shutil.copytree(FIXTURES / "project", project)
    sessions = tmp_path / "sessions"
    sessions.mkdir()
    session = sessions / "session.jsonl"
    session.write_text((FIXTURES / "session.jsonl").read_text().replace(FIXTURE_CWD, str(project)))
    return session


def replay_command(session: Path, theme: str = "deepwick", extra: tuple[str, ...] = (), theme_source: Path = THEME) -> str:
    cwd = json.loads(session.read_text().splitlines()[0])["cwd"]
    args = ["pi", *REPLAY_FLAGS, "--model", MODEL, "--theme", str(theme_source), "--use-theme", theme,
            "--session", str(session), *extra]
    return f"cd {shlex.quote(cwd)} && exec {shlex.join(args)}"


def _snapshot() -> tuple:
    files = []
    for sub in ("sessions", "themes"):
        root = AGENT_DIR / sub
        if root.is_dir():
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    stat = path.stat()
                    files.append((path.relative_to(AGENT_DIR).as_posix(), stat.st_size, stat.st_mtime_ns))
    settings = AGENT_DIR / "settings.json"
    return (settings.stat().st_mtime_ns if settings.exists() else None, tuple(files))


@contextmanager
def agent_dir_guard():
    before = _snapshot()
    yield
    assert _snapshot() == before, f"pi wrote to {AGENT_DIR} (settings.json, sessions/ or themes/)"
