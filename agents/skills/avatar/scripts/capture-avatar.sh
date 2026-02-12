#!/usr/bin/env bash
# capture-avatar.sh - Capture avatar renderer to v4l2loopback virtual camera
# Usage: ./capture-avatar.sh [OPTIONS]
#
# Options:
#   --auto          Auto-detect browser window (default)
#   --coords X,Y    Manual coordinates (e.g., --coords 100,100)
#   --size WxH      Video size (default: 1280x720)
#   --fps N         Frame rate (default: 20)
#   --device PATH   v4l2 device (default: /dev/video10)
#   --display :N    X display (default: :0)
#   --help          Show this help

set -euo pipefail

detect_v4l2_device() {
    for sysdir in /sys/class/video4linux/video*; do
        [ -d "$sysdir" ] || continue
        local deviceName
        deviceName=$(cat "$sysdir/name" 2>/dev/null || true)
        if echo "$deviceName" | grep -qi -e "avatar" -e "v4l2loopback"; then
            echo "/dev/$(basename "$sysdir")"
            return
        fi
    done
    echo "/dev/video10"
}

VIDEO_SIZE="1280x720"
FPS="20"
V4L2_DEVICE="$(detect_v4l2_device)"
DISPLAY_NUM=":0"
AUTO_DETECT=true
MANUAL_X=""
MANUAL_Y=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}+${NC} $*"; }
log_warn() { echo -e "${YELLOW}!${NC} $*"; }
log_error() { echo -e "${RED}x${NC} $*"; }

while [[ $# -gt 0 ]]; do
  case $1 in
    --auto)
      AUTO_DETECT=true
      shift
      ;;
    --coords)
      AUTO_DETECT=false
      IFS=',' read -r MANUAL_X MANUAL_Y <<< "$2"
      shift 2
      ;;
    --size)
      VIDEO_SIZE="$2"
      shift 2
      ;;
    --fps)
      FPS="$2"
      shift 2
      ;;
    --device)
      V4L2_DEVICE="$2"
      shift 2
      ;;
    --display)
      DISPLAY_NUM="$2"
      shift 2
      ;;
    --help)
      head -n 12 "$0" | tail -n +2
      exit 0
      ;;
    *)
      log_error "Unknown option: $1"
      echo "Run with --help for usage"
      exit 1
      ;;
  esac
done

log_info "Pre-flight checks..."

if ! lsmod | grep -q v4l2loopback; then
  log_error "v4l2loopback kernel module is not loaded"
  echo "Load with: sudo modprobe v4l2loopback devices=1 video_nr=10 card_label=\"Avatar Cam\" exclusive_caps=1"
  exit 1
fi
log_info "v4l2loopback is loaded"

if [[ ! -e "$V4L2_DEVICE" ]]; then
  log_error "Device $V4L2_DEVICE does not exist"
  ls -1 /dev/video* 2>/dev/null || echo "  (none found)"
  exit 1
fi
log_info "Device $V4L2_DEVICE exists"

if ! command -v ffmpeg &> /dev/null; then
  log_error "ffmpeg is not installed"
  exit 1
fi
log_info "ffmpeg is available"

if lsof "$V4L2_DEVICE" &> /dev/null; then
  log_warn "Device $V4L2_DEVICE is already in use:"
  lsof "$V4L2_DEVICE"
  echo ""
  read -p "Kill the process? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    lsof -t "$V4L2_DEVICE" | xargs kill -9
    log_info "Process killed"
  else
    log_error "Cannot proceed while device is busy"
    exit 1
  fi
fi

if [[ "$AUTO_DETECT" == true ]]; then
  log_info "Auto-detecting browser window..."

  if ! command -v xdotool &> /dev/null; then
    log_warn "xdotool not found, using (0,0) fallback"
    CAPTURE_X="0"
    CAPTURE_Y="0"
  else
    WINDOW_ID=$(xdotool search --name "localhost:3000" 2>/dev/null | head -1 || true)
    [[ -z "$WINDOW_ID" ]] && WINDOW_ID=$(xdotool search --name "Avatar" 2>/dev/null | head -1 || true)

    if [[ -z "$WINDOW_ID" ]]; then
      log_warn "Could not find browser window, using (0,0)"
      CAPTURE_X="0"
      CAPTURE_Y="0"
    else
      eval "$(xdotool getwindowgeometry --shell "$WINDOW_ID")"
      CAPTURE_X="$X"
      CAPTURE_Y="$Y"
      log_info "Found window at ${CAPTURE_X},${CAPTURE_Y} (${WIDTH}x${HEIGHT})"
    fi
  fi
else
  CAPTURE_X="$MANUAL_X"
  CAPTURE_Y="$MANUAL_Y"
  log_info "Using manual coordinates: ${CAPTURE_X},${CAPTURE_Y}"
fi

DISPLAY_INPUT="${DISPLAY_NUM}.0+${CAPTURE_X},${CAPTURE_Y}"

log_info "Starting capture..."
log_info "  Display: $DISPLAY_INPUT"
log_info "  Size: $VIDEO_SIZE"
log_info "  FPS: $FPS"
log_info "  Output: $V4L2_DEVICE"
echo ""
log_info "Press Ctrl+C to stop"
echo ""

cleanup() {
  log_warn "Stopping capture..."
  exit 0
}
trap cleanup SIGINT SIGTERM

ffmpeg \
  -f x11grab \
  -framerate "$FPS" \
  -video_size "$VIDEO_SIZE" \
  -i "$DISPLAY_INPUT" \
  -vf format=yuv420p \
  -f v4l2 \
  "$V4L2_DEVICE" \
  2>&1 | while read -r line; do
    if echo "$line" | grep -qE "(frame=|error|Error|failed|Failed)"; then
      echo "$line"
    fi
  done
