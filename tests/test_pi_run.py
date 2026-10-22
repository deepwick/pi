import getpass
import json
import socket
from pathlib import Path

import pytest

import pi_run
from pi_run import FIXTURES, MODEL, agent_dir_guard, prepare, replay_command


def test_replay_command_flags(tmp_path):
    command = replay_command(prepare(tmp_path))
    for flag in ("--offline", "--no-themes", "-ne", "-ns", "-np", "-nc", "--no-mcp", f"--model {MODEL}", "--use-theme deepwick", "--session"):
        assert f" {flag}" in command, flag
    assert "--session-dir" not in command
    assert "~/.pi" not in command and ".pi/agent" not in command


def test_replay_command_runs_in_session_cwd(tmp_path):
    command = replay_command(prepare(tmp_path))
    assert command.startswith(f"cd {tmp_path / 'project'} && ")


def test_prepare_rewrites_cwd(tmp_path):
    text = prepare(tmp_path).read_text()
    assert "/home/user/project" not in text
    assert str(tmp_path / "project") in text
    assert json.loads(text.splitlines()[0])["cwd"] == str(tmp_path / "project")
    assert (tmp_path / "project/sample.py").is_file()


def test_fixture_is_scrubbed():
    private = [getpass.getuser(), socket.gethostname(), str(Path.home()), "otari.staph"]
    for path in FIXTURES.rglob("*"):
        if path.is_file():
            text = path.read_text()
            for needle in private:
                assert needle not in text, (path.name, needle)


def test_guard_detects_settings_change(tmp_path, monkeypatch):
    monkeypatch.setattr(pi_run, "AGENT_DIR", tmp_path)
    (tmp_path / "settings.json").write_text("{}")
    with pytest.raises(AssertionError):
        with agent_dir_guard():
            (tmp_path / "settings.json").write_text('{"theme": "deepwick"}')


def test_guard_detects_new_session(tmp_path, monkeypatch):
    monkeypatch.setattr(pi_run, "AGENT_DIR", tmp_path)
    (tmp_path / "settings.json").write_text("{}")
    with pytest.raises(AssertionError):
        with agent_dir_guard():
            (tmp_path / "sessions/x").mkdir(parents=True)
            (tmp_path / "sessions/x/s.jsonl").write_text("{}")


def test_guard_ignores_lock_file_churn(tmp_path, monkeypatch):
    monkeypatch.setattr(pi_run, "AGENT_DIR", tmp_path)
    (tmp_path / "settings.json").write_text("{}")
    with agent_dir_guard():
        (tmp_path / "lock").write_text("")
        (tmp_path / "lock").unlink()


def test_replay_command_without_theme_source(tmp_path):
    assert "--theme" not in replay_command(prepare(tmp_path), theme_source=None).replace("--use-theme", "")
