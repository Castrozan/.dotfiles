#!/usr/bin/env bash
# faster-whisper wrapper for OpenClaw media transcription

LOGFILE="/tmp/faster-whisper-debug.log"
echo "=== $(date -Iseconds) PID=$$ ===" >> "$LOGFILE"
echo "ARGS: $*" >> "$LOGFILE"
echo "ENV: HOME=${HOME:-unset} PATH=${PATH:-unset}" >> "$LOGFILE"

INPUT_FILE="${1:-}"
shift || true

MODEL="tiny"
OUTPUT_DIR="/tmp/whisper-out"
OUTPUT_FORMAT="txt"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="${2:-tiny}"; shift 2 ;;
    --output_dir) OUTPUT_DIR="${2:-/tmp/whisper-out}"; shift 2 ;;
    --output_format) OUTPUT_FORMAT="${2:-txt}"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$INPUT_FILE" ]]; then
  echo "ERROR: no input file" >> "$LOGFILE"
  echo "ERROR: no input file" >&2
  exit 1
fi

export HOME="${HOME:-@homePath@}"
export LD_LIBRARY_PATH="/nix/store/xm08aqdd7pxcdhm0ak6aqb1v7hw5q6ri-gcc-14.3.0-lib/lib:/nix/store/yil5gzi7sxmx5jn90883daa4rj03bf8b-home-manager-path/lib"

VENV_DIR="${HOME}/.local/share/hey-cleber-venv"
export PATH="${VENV_DIR}/bin:${PATH}"
export VIRTUAL_ENV="${VENV_DIR}"

mkdir -p "$OUTPUT_DIR"

BASENAME=$(basename "$INPUT_FILE")
BASENAME_NO_EXT="${BASENAME%.*}"
OUTPUT_FILE="${OUTPUT_DIR}/${BASENAME_NO_EXT}.${OUTPUT_FORMAT}"

echo "INPUT=$INPUT_FILE OUTPUT=$OUTPUT_FILE VENV=$VENV_DIR" >> "$LOGFILE"
echo "python3=$(ls -la "${VENV_DIR}/bin/python3" 2>&1)" >> "$LOGFILE"

"${VENV_DIR}/bin/python3" -c "
import sys
from faster_whisper import WhisperModel
model = WhisperModel('${MODEL}', device='cpu', compute_type='int8')
segments, info = model.transcribe('${INPUT_FILE}')
text = ' '.join(s.text for s in segments).strip()
with open('${OUTPUT_FILE}', 'w') as f:
    f.write(text + '\n')
print(text)
" 2>> "$LOGFILE"
PYEXIT=$?
echo "python exit=$PYEXIT" >> "$LOGFILE"
exit $PYEXIT
