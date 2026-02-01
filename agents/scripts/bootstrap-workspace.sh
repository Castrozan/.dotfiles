#!/usr/bin/env bash
set -euo pipefail

WS="${1:?Usage: bootstrap-workspace.sh <workspace-path>}"

mkdir -p "$WS/memory" "$WS/projects" "$WS/research"

if [ ! -f "$WS/MEMORY.md" ]; then
  cat > "$WS/MEMORY.md" << 'INITIAL'
# MEMORY.md — Long-Term Memory

_No memories yet. This file will be populated as I learn._
INITIAL
fi

if [ ! -f "$WS/TOOLS.md" ]; then
  cat > "$WS/TOOLS.md" << 'INITIAL'
# TOOLS.md - Local Notes

_Operational notes will be added here as tools are configured._
INITIAL
fi

if [ ! -f "$WS/HEARTBEAT.md" ]; then
  cat > "$WS/HEARTBEAT.md" << 'INITIAL'
# HEARTBEAT.md

_No active heartbeat tasks._
INITIAL
fi
