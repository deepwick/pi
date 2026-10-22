#!/usr/bin/env bash
# Replay the fixture session in Ptyxis (off-screen, via the workspace's tools/ptyxis-shot) and save screenshot.png.
# HOME points at a temp dir so the footer shows ~/project; PI_CODING_AGENT_DIR keeps pi on the real agent dir.
# SHOT_SIZE (default 1280x800, vshot's) sets the window; the crop drops Ptyxis's 50 px header bar unless
# SHOT_CROP is given. SHOT_DRY_RUN=1 prints "SHOT_SIZE SHOT_CROP" and exits.
set -euo pipefail
size="${SHOT_SIZE:-1280x800}"
crop="${SHOT_CROP:-${size%x*}x$((${size#*x} - 50))+0+50}"
if [[ -n ${SHOT_DRY_RUN:-} ]]; then
  echo "$size $crop"
  exit 0
fi
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
SHOT_MAXIMIZE=1 SHOT_SIZE="$size" SHOT_CROP="$crop" SHOT_DELAY="${SHOT_DELAY:-8}" "$ws/tools/ptyxis-shot" "$repo/screenshot.png" -- \
  env HOME="$tmp/home" PI_CODING_AGENT_DIR="$HOME/.pi/agent" PATH="$node_dir:$PATH" COLORTERM=truecolor \
  bash -c "$cmd"
