#!/usr/bin/env bash
# Replay the fixture session in Ptyxis (off-screen, via the workspace's tools/ptyxis-shot) and save screenshot.png.
# HOME points at a temp dir so the footer shows ~/project; PI_CODING_AGENT_DIR keeps pi on the real agent dir.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"
ws="$(cd "$repo/.." && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
node_dir="$(dirname "$(realpath "$(command -v node)")")"
cmd="$(cd "$repo" && PYTHONPATH="$ws/spec:tests" python3 -c '
import sys
from pathlib import Path
from pi_run import prepare, replay_command
print(replay_command(prepare(Path(sys.argv[1]))))
' "$tmp/home")"
cmd="${cmd/exec pi /exec $HOME/.pi/agent/bin/pi }"
SHOT_MAXIMIZE=1 SHOT_CROP=1280x750+0+50 SHOT_DELAY="${SHOT_DELAY:-8}" "$ws/tools/ptyxis-shot" "$repo/screenshot.png" -- \
  env HOME="$tmp/home" PI_CODING_AGENT_DIR="$HOME/.pi/agent" PATH="$node_dir:$PATH" COLORTERM=truecolor \
  bash -c "$cmd"
