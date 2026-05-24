#!/usr/bin/env bash

_run_docker_integration_tests() {
	if ! command -v docker &>/dev/null; then
		echo "WARN: docker not installed, skipping docker integration tests" >&2
		return 0
	fi
	if ! command -v bats &>/dev/null; then
		echo "WARN: bats not installed, skipping docker integration tests" >&2
		return 0
	fi

	echo "--- Docker Integration Tests ---"
	local dockerTestFiles
	dockerTestFiles=$(find "$REPO_DIR/home/base" "$REPO_DIR/home/linux" "$REPO_DIR/home/darwin" -path "*/tests/*-docker.bats" -type f | sort)

	if [[ -z "$dockerTestFiles" ]]; then
		echo "No docker test files found"
		return 0
	fi

	bats $dockerTestFiles
	echo ""
}
