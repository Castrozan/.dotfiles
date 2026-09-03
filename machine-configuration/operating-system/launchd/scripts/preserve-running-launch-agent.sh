set -euo pipefail

launch_agent_label="$1"
source_property_list="$2"
destination_property_list="$3"
runtime_root_directory="$4"
launch_agent_domain="gui/$(id -u)"

if cmp -s "$source_property_list" "$destination_property_list"; then
	exit 0
fi

if ! loaded_launch_agent="$(launchctl print "$launch_agent_domain/$launch_agent_label" 2>/dev/null)"; then
	exit 0
fi

while IFS= read -r loaded_store_path; do
	if [[ -z "$loaded_store_path" ]]; then
		continue
	fi
	mkdir -p "$runtime_root_directory"
	runtime_root_path="$runtime_root_directory/$(basename "$loaded_store_path")"
	nix-store --realise "$loaded_store_path" --add-root "$runtime_root_path" --indirect >/dev/null
done < <(printf '%s\n' "$loaded_launch_agent" | grep -Eo '/nix/store/[0-9a-z]{32}-[^/[:space:]<>&"]+' | sort -u || true)

install -Dm444 -T "$source_property_list" "$destination_property_list"
