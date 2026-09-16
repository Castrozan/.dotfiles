#!/usr/bin/env bash

set -Eeuo pipefail

currentScriptDirectoryPath="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly currentScriptDirectoryPath

baseCavaConfigurationPath="${currentScriptDirectoryPath}/../assets/cava-bar.conf"
readonly baseCavaConfigurationPath

main() {
	local preferredPulseMonitorSourceName
	preferredPulseMonitorSourceName="$(_detectPreferredPulseMonitorSourceName)"
	_runCavaWithResolvedConfiguration "$preferredPulseMonitorSourceName"
}

_detectPreferredPulseMonitorSourceName() {
	local firstRunningSinkMonitorSourceName
	local firstActiveSinkInputMonitorSourceName
	local firstAvailableMonitorSourceName
	local defaultSinkMonitorSourceName

	firstRunningSinkMonitorSourceName="$(_findFirstRunningSinkMonitorSourceName)"
	if [ -n "$firstRunningSinkMonitorSourceName" ]; then
		printf '%s\n' "$firstRunningSinkMonitorSourceName"
		return 0
	fi

	firstActiveSinkInputMonitorSourceName="$(_findFirstActiveSinkInputMonitorSourceName)"
	if [ -n "$firstActiveSinkInputMonitorSourceName" ]; then
		printf '%s\n' "$firstActiveSinkInputMonitorSourceName"
		return 0
	fi

	firstAvailableMonitorSourceName="$(_findFirstAvailableMonitorSourceName)"
	if [ -n "$firstAvailableMonitorSourceName" ]; then
		printf '%s\n' "$firstAvailableMonitorSourceName"
		return 0
	fi

	defaultSinkMonitorSourceName="$(_buildDefaultSinkMonitorSourceName)"
	if [ -n "$defaultSinkMonitorSourceName" ] && _pulseSourceNameExists "$defaultSinkMonitorSourceName"; then
		printf '%s\n' "$defaultSinkMonitorSourceName"
		return 0
	fi

	printf 'auto\n'
}

_findFirstRunningSinkMonitorSourceName() {
	_listShortPulseSinks | awk '$NF == "RUNNING" { print $2 ".monitor"; exit }'
}

_findFirstActiveSinkInputMonitorSourceName() {
	local preferredSinkIdentifier
	preferredSinkIdentifier="$(_listShortPulseSinkInputs | awk '$2 != "" { print $2; exit }')"

	if [ -z "$preferredSinkIdentifier" ]; then
		return 0
	fi

	_listShortPulseSinks | awk -v preferredSinkIdentifier="$preferredSinkIdentifier" '$1 == preferredSinkIdentifier { print $2 ".monitor"; exit }'
}

_findFirstAvailableMonitorSourceName() {
	_listShortPulseSources | awk '$2 ~ /\.monitor$/ { print $2; exit }'
}

_buildDefaultSinkMonitorSourceName() {
	local defaultSinkName
	defaultSinkName="$(_readDefaultSinkName)"

	if [ -z "$defaultSinkName" ]; then
		return 0
	fi

	printf '%s.monitor\n' "$defaultSinkName"
}

_readDefaultSinkName() {
	pactl get-default-sink 2>/dev/null || true
}

_pulseSourceNameExists() {
	local pulseSourceName=$1
	_listShortPulseSources | awk -v pulseSourceName="$pulseSourceName" '$2 == pulseSourceName { found = 1 } END { exit(found ? 0 : 1) }'
}

_listShortPulseSources() {
	pactl list short sources 2>/dev/null || true
}

_listShortPulseSinks() {
	pactl list short sinks 2>/dev/null || true
}

_listShortPulseSinkInputs() {
	pactl list short sink-inputs 2>/dev/null || true
}

_runCavaWithResolvedConfiguration() {
	local preferredPulseMonitorSourceName=$1
	exec cava -p <(_printRuntimeCavaConfiguration "$preferredPulseMonitorSourceName")
}

_printRuntimeCavaConfiguration() {
	local preferredPulseMonitorSourceName=$1
	cat "$baseCavaConfigurationPath"
	printf '\n[input]\nmethod = pulse\nsource = %s\n' "$preferredPulseMonitorSourceName"
}

main "$@"
