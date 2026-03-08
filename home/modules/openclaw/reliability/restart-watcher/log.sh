#!/usr/bin/env bash

set -Eeuo pipefail

_log() {
	echo "[restart-watcher] $(date -Iseconds) $*"
}
