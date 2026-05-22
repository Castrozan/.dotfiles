# shellcheck shell=bash
# Betha Marketplace lifecycle verbs (wipe / install / status / verify /
# trigger-clone). Sourced from `scripts/vscode`.

# Locations that the BMU extension and the chat.plugins.marketplaces system
# touch on a Linux install. The wipe verb removes anything below these paths
# that the marketplace owns; `_betha_marketplace_overrides` in mcp.json is
# user data and survives.
_BETHA_MARKETPLACE_EXTENSION_ID="betha-sistemas.betha-marketplace-updater"
_BETHA_MARKETPLACE_AGENT_PLUGINS_DIR="$HOME/.vscode/agent-plugins"
_BETHA_MARKETPLACE_FEDERATION_CACHE_PARENT="$HOME/.vscode/agent-plugins/gitlab.services.betha.cloud/betha-ai"
_BETHA_MARKETPLACE_USER_MCP_JSON="$HOME/.config/Code/User/mcp.json"
_BETHA_MARKETPLACE_INSTALLED_JSON="$HOME/.vscode/agent-plugins/installed.json"
_BETHA_MARKETPLACE_INSTALL_URL_DEFAULT="https://betha-ai-marketplace-412a34.gitlab.services.betha.cloud/install.js"

_verb_betha_marketplace() {
	local subverb="${1:-}"
	shift || true
	case "$subverb" in
	wipe) _verb_betha_marketplace_wipe "$@" ;;
	install) _verb_betha_marketplace_install "$@" ;;
	status) _verb_betha_marketplace_status "$@" ;;
	verify) _verb_betha_marketplace_verify "$@" ;;
	trigger-clone) _verb_betha_marketplace_trigger_clone "$@" ;;
	*)
		echo "Unknown betha-marketplace subverb: ${subverb:-(none)} (use: wipe, install, status, verify, trigger-clone)" >&2
		exit 1
		;;
	esac
}

_verb_betha_marketplace_wipe() {
	echo "[1/4] uninstalling extension ${_BETHA_MARKETPLACE_EXTENSION_ID}"
	code --uninstall-extension "$_BETHA_MARKETPLACE_EXTENSION_ID" 2>/dev/null | tail -1 || true

	if [[ -f "$_BETHA_MARKETPLACE_USER_MCP_JSON" ]]; then
		echo "[2/4] wiping _betha_marketplace-owned servers/inputs (preserving overrides + user-added servers)"
		local tmp="${_BETHA_MARKETPLACE_USER_MCP_JSON}.wipe.${$}.tmp"
		jq '
			._betha_marketplace as $owned
			| .servers = ((.servers // {}) | with_entries(select(.key as $k | ($owned.serverNames // []) | index($k) | not)))
			| .inputs = ((.inputs // []) | map(select(.id as $i | ($owned.inputIds // []) | index($i) | not)))
			| del(._betha_marketplace)
		' "$_BETHA_MARKETPLACE_USER_MCP_JSON" >"$tmp"
		mv "$tmp" "$_BETHA_MARKETPLACE_USER_MCP_JSON"
	fi

	echo "[3/4] removing federation cache dirs under ${_BETHA_MARKETPLACE_FEDERATION_CACHE_PARENT}"
	rm -rf \
		"${_BETHA_MARKETPLACE_FEDERATION_CACHE_PARENT}/betha.ai-marketplace" \
		"${_BETHA_MARKETPLACE_FEDERATION_CACHE_PARENT}/betha.ai-marketplace-test"

	if [[ -f "$_BETHA_MARKETPLACE_INSTALLED_JSON" ]]; then
		echo "[4/4] removing installed.json entries pointing at wiped federations"
		local tmp="${_BETHA_MARKETPLACE_INSTALLED_JSON}.wipe.${$}.tmp"
		jq '.installed = ((.installed // []) | map(select(.marketplace and (.marketplace | contains("betha.ai-marketplace") | not))))' \
			"$_BETHA_MARKETPLACE_INSTALLED_JSON" >"$tmp"
		mv "$tmp" "$_BETHA_MARKETPLACE_INSTALLED_JSON"
	fi

	echo "wipe complete."
}

_verb_betha_marketplace_install() {
	local install_url="${BETHA_MARKETPLACE_INSTALL_URL:-$_BETHA_MARKETPLACE_INSTALL_URL_DEFAULT}"
	echo "running install.js from ${install_url}"
	node -e "fetch('${install_url}').then(r=>r.text()).then(eval)"
}

_verb_betha_marketplace_trigger_clone() {
	# Canonical path that VS Code's chat.plugins.marketplaces federation
	# system listens to: open the Extensions view, then type @agentPlugins
	# into its Monaco-backed search input. The filter materialisation forces
	# VS Code to clone every registered marketplace whose cache dir is
	# missing. README Passo 5 step.
	_assert_running
	local wait_timeout_seconds="${1:-90}"
	echo "[1/3] focusing Extensions view"
	_python_helper "command_by_title" --command-title "Extensions: Focus on Extensions View" >/dev/null
	sleep 1
	echo "[2/3] typing @agentPlugins into the Extensions search (Monaco editor — needs type-focused)"
	uv run --quiet --script "$LIB_DIR/cdp_type_focused.py" --port "$CDP_PORT" --text "@agentPlugins" >/dev/null
	echo "[3/3] waiting up to ${wait_timeout_seconds}s for federation cache to materialise"
	local cache_dir="${_BETHA_MARKETPLACE_FEDERATION_CACHE_PARENT}/betha.ai-marketplace"
	local elapsed=0
	while ((elapsed < wait_timeout_seconds)); do
		if [[ -f "${cache_dir}/build-metadata.json" ]]; then
			echo "federation cloned (after ${elapsed}s)"
			return 0
		fi
		sleep 3
		elapsed=$((elapsed + 3))
	done
	echo "federation cache still absent after ${wait_timeout_seconds}s — check chat.plugins.marketplaces setting and SSH connectivity" >&2
	exit 1
}

_verb_betha_marketplace_status() {
	# `local x=$(pipeline)` masks the substitution exit code, so set -e +
	# pipefail does not kill us when grep finds no match (the no-extension-
	# installed case is normal, not error). Splitting declaration and
	# assignment would propagate the failure and silently abort the verb.
	local installed_extension_version="$(code --list-extensions --show-versions 2>/dev/null | grep -E "^${_BETHA_MARKETPLACE_EXTENSION_ID}@" | head -1 | awk -F'@' '{print $2}')"

	local federation_cache_dir="${_BETHA_MARKETPLACE_FEDERATION_CACHE_PARENT}/betha.ai-marketplace"
	local federation_version="absent"
	local vsix_in_federation_cache="absent"
	if [[ -d "$federation_cache_dir" ]]; then
		federation_version="$(jq -r '.version // "unknown"' "${federation_cache_dir}/build-metadata.json" 2>/dev/null || echo unknown)"
		local -a vsix_candidates=("${federation_cache_dir}"/tools/vscode-extension/dist/*.vsix)
		if [[ -f "${vsix_candidates[0]}" ]]; then
			vsix_in_federation_cache="$(basename "${vsix_candidates[0]}")"
		fi
	fi

	local owned_mcp_servers_json="[]"
	local user_overrides_json="[]"
	if [[ -f "$_BETHA_MARKETPLACE_USER_MCP_JSON" ]]; then
		owned_mcp_servers_json="$(jq -c '._betha_marketplace.serverNames // []' "$_BETHA_MARKETPLACE_USER_MCP_JSON")"
		user_overrides_json="$(jq -c '(._betha_marketplace_overrides // {}) | keys' "$_BETHA_MARKETPLACE_USER_MCP_JSON")"
	fi

	local installed_plugin_count=0
	if [[ -f "$_BETHA_MARKETPLACE_INSTALLED_JSON" ]]; then
		installed_plugin_count="$(jq '.installed | length' "$_BETHA_MARKETPLACE_INSTALLED_JSON")"
	fi

	jq -n \
		--arg extension_version "${installed_extension_version:-absent}" \
		--arg federation_version "$federation_version" \
		--arg vsix_in_federation_cache "$vsix_in_federation_cache" \
		--argjson owned_mcp_servers "$owned_mcp_servers_json" \
		--argjson user_overrides "$user_overrides_json" \
		--argjson installed_plugin_count "$installed_plugin_count" \
		'{
			extension_version: $extension_version,
			federation_version: $federation_version,
			vsix_in_federation_cache: $vsix_in_federation_cache,
			installed_plugin_count: $installed_plugin_count,
			owned_mcp_servers: $owned_mcp_servers,
			user_overrides: $user_overrides
		}'
}

_verb_betha_marketplace_verify() {
	local status_json
	status_json="$(_verb_betha_marketplace_status)"
	echo "$status_json" | jq .

	local extension_version federation_version vsix_in_federation_cache
	extension_version="$(echo "$status_json" | jq -r '.extension_version')"
	federation_version="$(echo "$status_json" | jq -r '.federation_version')"
	vsix_in_federation_cache="$(echo "$status_json" | jq -r '.vsix_in_federation_cache')"

	local all_ok=1
	[[ "$extension_version" == "absent" ]] && {
		echo "FAIL: extension not installed" >&2
		all_ok=0
	}
	[[ "$federation_version" == "absent" ]] && {
		echo "FAIL: federation cache absent — VS Code has not yet cloned the marketplace branch" >&2
		all_ok=0
	}
	[[ "$vsix_in_federation_cache" == "absent" ]] && {
		echo "WARN: marketplace branch does not carry the extension VSIX — selfUpdate.ts will not detect new extension versions (fixed in marketplace v2.8.2)" >&2
	}

	if ((all_ok == 0)); then
		exit 1
	fi
	echo "verify: OK"
}
