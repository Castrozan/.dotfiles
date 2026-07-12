dotfiles_directory="${1:-$HOME/.dotfiles}"
themes_directory="${dotfiles_directory}/static/themes"

if [[ ! -d "$themes_directory" ]]; then
	exit 0
fi

shopt -s nullglob
for wallpaper_derived_marker in "$themes_directory"/*/wallpaper-derived.mode; do
	theme_directory="$(dirname "$wallpaper_derived_marker")"
	theme_name="$(basename "$theme_directory")"
	backgrounds_directory="${theme_directory}/backgrounds"
	colors_toml_path="${theme_directory}/colors.toml"

	if [[ ! -d "$backgrounds_directory" ]]; then
		continue
	fi

	active_wallpaper_path="$(find "$backgrounds_directory" -maxdepth 1 -type f | sort | head -n 1)"
	if [[ -z "$active_wallpaper_path" ]]; then
		continue
	fi

	if [[ -f "$colors_toml_path" && ! "$active_wallpaper_path" -nt "$colors_toml_path" ]]; then
		continue
	fi

	regenerated_colors_toml_tempfile="$(mktemp)"
	theme-colors-from-wallpaper "$active_wallpaper_path" >"$regenerated_colors_toml_tempfile"

	if [[ -f "$colors_toml_path" ]] && cmp -s "$regenerated_colors_toml_tempfile" "$colors_toml_path"; then
		rm -f "$regenerated_colors_toml_tempfile"
		touch "$colors_toml_path"
		continue
	fi

	mv "$regenerated_colors_toml_tempfile" "$colors_toml_path"
	git -C "$dotfiles_directory" add "$colors_toml_path"
	echo "theme: regenerated ${theme_name}/colors.toml from $(basename "$active_wallpaper_path")" >&2
done
