#!/usr/bin/env bash
set -euo pipefail

launcher_directory="$1"
crudini_executable="$2"
mkdir -p "$launcher_directory"
"$crudini_executable" --set --ini-options=nospace "$launcher_directory/prismlauncher.cfg" General UseDiscreteGpu true

for instance_configuration in "$launcher_directory"/instances/*/instance.cfg; do
	[ -f "$instance_configuration" ] || continue
	"$crudini_executable" --set --ini-options=nospace "$instance_configuration" General UseDiscreteGpu true
	instance_wrapper_command="$("$crudini_executable" --get "$instance_configuration" General WrapperCommand 2>/dev/null || true)"
	case "$instance_wrapper_command" in
	'"env -u __GLX_VENDOR_LIBRARY_NAME -u GBM_BACKEND -u __NV_PRIME_RENDER_OFFLOAD -u __NV_PRIME_RENDER_OFFLOAD_PROVIDER -u __VK_LAYER_NV_optimus DRI_PRIME=pci-0000_05_00_0"')
		"$crudini_executable" --set --ini-options=nospace "$instance_configuration" General WrapperCommand ""
		;;
	esac
done
