#!/usr/bin/env bash
set -euo pipefail

export PATH="@aerospaceBinPath@:${PATH}"

workspace_slots_per_page=7

focused_workspace="$(aerospace list-workspaces --focused 2>/dev/null || true)"
if [ -z "${focused_workspace}" ]; then
	focused_workspace=1
fi

page_index=$(((focused_workspace - 1) / workspace_slots_per_page))
first_workspace_on_page=$((page_index * workspace_slots_per_page + 1))
last_workspace_on_page=$((first_workspace_on_page + workspace_slots_per_page - 1))

menu_bar_segments=()
for workspace_id in $(seq "${first_workspace_on_page}" "${last_workspace_on_page}"); do
	if [ "${workspace_id}" -eq "${focused_workspace}" ]; then
		menu_bar_segments+=("[${workspace_id}]")
	else
		menu_bar_segments+=("${workspace_id}")
	fi
done

printf '%s' "${menu_bar_segments[*]}"
echo " | font=Menlo size=13"

echo "---"
for workspace_id in $(seq 1 "${workspace_slots_per_page}"); do
	echo "Workspace ${workspace_id} | bash=aerospace param1=workspace param2=${workspace_id} terminal=false refresh=true"
done
