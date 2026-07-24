#!/usr/bin/env bash

DOCKER_TEST_REPOSITORY_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
readonly DOCKER_TEST_REPOSITORY_ROOT
readonly DOCKER_TEST_IMAGE_DOCKERFILE="$DOCKER_TEST_REPOSITORY_ROOT/__tests__/Dockerfile"

docker_daemon_is_reachable() {
	command -v docker &>/dev/null && docker info &>/dev/null
}

skip_unless_docker_daemon_is_reachable() {
	if ! docker_daemon_is_reachable; then
		skip "docker daemon not reachable; start Docker Desktop on darwin or the docker service on NixOS"
	fi
}

build_privileged_test_image_or_fail() {
	local imageTag="$1"
	local buildOutput
	if ! buildOutput=$(docker build -t "$imageTag" -f "$DOCKER_TEST_IMAGE_DOCKERFILE" "$DOCKER_TEST_REPOSITORY_ROOT" 2>&1); then
		echo "docker build failed for $imageTag using $DOCKER_TEST_IMAGE_DOCKERFILE" >&2
		echo "$buildOutput" >&2
		return 1
	fi
}

privileged_container_can_write_kernel_network_settings() {
	local imageTag="$1"
	docker run --rm --privileged "$imageTag" bash -c \
		'echo 212992 > /proc/sys/net/core/rmem_max && echo bbr > /proc/sys/net/ipv4/tcp_congestion_control' &>/dev/null
}

skip_unless_privileged_container_can_write_kernel_network_settings() {
	local imageTag="$1"
	if ! privileged_container_can_write_kernel_network_settings "$imageTag"; then
		skip "this docker host refuses privileged net.core and tcp_congestion_control writes; the Docker Desktop VM on darwin namespaces them away, so these live-kernel assertions need a Linux docker host"
	fi
}

remove_test_image_if_present() {
	local imageTag="$1"
	if docker_daemon_is_reachable; then
		docker rmi -f "$imageTag" &>/dev/null || true
	fi
}
