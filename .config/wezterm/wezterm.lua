local wezterm = require("wezterm")

local is_darwin = wezterm.target_triple:find("darwin") ~= nil

local theme_colors_path = os.getenv("HOME") .. "/.config/hypr-theme/current/theme/wezterm-colors.lua"
wezterm.add_to_config_reload_watch_list(theme_colors_path)

local theme_colors_file = io.open(theme_colors_path, "r")
local hypr_theme_colors
if theme_colors_file then
	theme_colors_file:close()
	hypr_theme_colors = dofile(theme_colors_path)
end

local mux = wezterm.mux
wezterm.on("gui-startup", function(cmd)
	local tab, pane, window = mux.spawn_window(cmd or {})
	window:gui_window():maximize()
end)

if type(mux.get_active_window) == "function" then
	wezterm.on("gui-attached", function(domain)
		local window = mux.get_active_window()
		if window then
			window:gui_window():maximize()
		end
	end)
end

local config = {
	font = wezterm.font_with_fallback({
		"MonaspiceNe Nerd Font Mono",
		"FiraCode Nerd Font Mono",
		"Noto Color Emoji",
	}),
	font_size = is_darwin and 18 or 16,

	window_padding = {
		left = 10,
		right = 10,
		top = 10,
		bottom = 10,
	},

	max_fps = 120,
	front_end = is_darwin and "WebGpu" or "OpenGL",
	window_decorations = "RESIZE",
	use_resize_increments = false,
	adjust_window_size_when_changing_font_size = false,
	window_background_opacity = 0.85,
	text_background_opacity = 0.75,
	macos_window_background_blur = 20,

	enable_tab_bar = false,
	hide_tab_bar_if_only_one_tab = true,

	audible_bell = "Disabled",

	warn_about_missing_glyphs = false,
	freetype_load_target = "Light",
	scrollback_lines = 10000,
	default_prog = is_darwin and { "/run/current-system/sw/bin/bash", "-l" } or { "bash", "-l" },
	default_cwd = wezterm.home_dir,

	term = "wezterm",
	enable_csi_u_key_encoding = true,

	bypass_mouse_reporting_modifiers = "CTRL",

	mouse_bindings = {
		{
			event = { Up = { streak = 1, button = "Left" } },
			mods = "CTRL",
			action = wezterm.action.OpenLinkAtMouseCursor,
		},
		{
			event = { Down = { streak = 1, button = "Left" } },
			mods = "CTRL",
			action = wezterm.action.Nop,
		},
		{
			event = { Up = { streak = 1, button = "Left" } },
			mods = "CTRL",
			action = wezterm.action.OpenLinkAtMouseCursor,
			mouse_reporting = true,
		},
		{
			event = { Down = { streak = 1, button = "Left" } },
			mods = "CTRL",
			action = wezterm.action.Nop,
			mouse_reporting = true,
		},
	},

	keys = {
		{ key = "Enter", mods = "SHIFT", action = wezterm.action.SendString("\x1b[13;2u") },
		{ key = "Enter", mods = "CTRL", action = wezterm.action.SendString("\x1b[13;5u") },
		{ key = "Enter", mods = "ALT", action = wezterm.action.SendString("\x1b[13;3u") },
		{ key = "Space", mods = "CTRL", action = wezterm.action.SendString("\x00") },
		{
			key = "s",
			mods = "CTRL|SHIFT",
			action = wezterm.action.SendString("herdr\n"),
		},
		{ key = "f", mods = "CTRL|SHIFT", action = wezterm.action.DisableDefaultAssignment },
		{ key = "k", mods = "CTRL|SHIFT", action = wezterm.action.DisableDefaultAssignment },
		{ key = "p", mods = "CTRL|SHIFT", action = wezterm.action.DisableDefaultAssignment },
		{ key = "UpArrow", mods = "CTRL|SHIFT", action = wezterm.action.SendString("\x1b[1;6A") },
		{ key = "DownArrow", mods = "CTRL|SHIFT", action = wezterm.action.SendString("\x1b[1;6B") },
		{ key = "PageUp", mods = "CTRL", action = wezterm.action.SendString("\x02p") },
		{ key = "PageDown", mods = "CTRL", action = wezterm.action.SendString("\x02n") },
		{ key = "w", mods = "CTRL|SHIFT", action = wezterm.action.CloseCurrentTab({ confirm = false }) },
	},

	initial_cols = 300,
	initial_rows = 100,

	window_close_confirmation = "NeverPrompt",
}

if is_darwin then
	table.insert(config.keys, { key = "w", mods = "CMD", action = wezterm.action.CloseCurrentTab({ confirm = false }) })
end

if hypr_theme_colors then
	config.color_schemes = { ["HyprTheme"] = hypr_theme_colors }
	config.color_scheme = "HyprTheme"
end

return config
