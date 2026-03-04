#!/usr/bin/env bash

set -Eeuo pipefail

_log() {
	echo "[timeout-recovery] $(date -Iseconds) $*"
}
