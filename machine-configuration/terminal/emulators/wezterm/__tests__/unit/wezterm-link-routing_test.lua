local configuration_path = arg[0]:match("^(.*)/__tests__/unit/") .. "/program-configuration/wezterm.lua"

local function load_configuration(target_triple)
	local events = {}
	local launches = {}
	package.loaded.wezterm = {
		target_triple = target_triple,
		home_dir = "/tmp",
		mux = {},
		action = setmetatable({}, {
			__index = function(actions, name)
				local action = function(arguments)
					return { name = name, arguments = arguments }
				end
				rawset(actions, name, action)
				return action
			end,
		}),
		add_to_config_reload_watch_list = function() end,
		font_with_fallback = function(fonts)
			return fonts
		end,
		on = function(name, handler)
			events[name] = handler
		end,
		background_child_process = function(arguments)
			table.insert(launches, arguments)
		end,
	}
	return dofile(configuration_path), events, launches
end

local function open_link(events, launches, modifiers, uri)
	local window = {
		keyboard_modifiers = function()
			return modifiers, ""
		end,
	}
	assert(events["open-uri"](window, {}, uri) == false)
	assert(#launches == 1)
	return launches[1]
end

for _, modifiers in ipairs({ "CTRL|SUPER", "SUPER|CTRL" }) do
	local _, events, launches = load_configuration("aarch64-apple-darwin")
	local uri = "https://example.com/personal?value='quoted'&literal=$(false)"
	local launch = open_link(events, launches, modifiers, uri)
	assert(launch[3] == 'exec summon-chrome-personal-profile "$1"', "Ctrl+Super must open the personal profile")
	assert(launch[5] == uri, "the URL must remain a separate, unchanged argument")
end

for _, modifiers in ipairs({ "CTRL", "SUPER", "NONE" }) do
	local _, events, launches = load_configuration("aarch64-apple-darwin")
	local launch = open_link(events, launches, modifiers, "https://example.com/work")
	assert(launch[3] == 'exec summon-chrome-work-profile "$1"', "other link gestures must keep the work profile")
end

for _, modifiers in ipairs({ "CTRL", "CTRL|SUPER" }) do
	local _, events, launches = load_configuration("x86_64-unknown-linux-gnu")
	local uri = "https://example.com/default"
	local launch = open_link(events, launches, modifiers, uri)
	assert(#launch == 2 and launch[1] == "xdg-open" and launch[2] == uri)
end

local configuration = load_configuration("aarch64-apple-darwin")
for _, modifiers in ipairs({ "CTRL", "CTRL|SUPER" }) do
	for _, mouse_reporting in ipairs({ false, true }) do
		local matches = {}
		for _, binding in ipairs(configuration.mouse_bindings) do
			if binding.mods == modifiers and (binding.mouse_reporting or false) == mouse_reporting then
				for _, event_name in ipairs({ "Up", "Down" }) do
					local event = binding.event[event_name]
					if event and event.button == "Left" and event.streak == 1 then
						matches[event_name] = binding.action
					end
				end
			end
		end
		assert(matches.Up == package.loaded.wezterm.action.OpenLinkAtMouseCursor, modifiers .. " must open links")
		assert(matches.Down == package.loaded.wezterm.action.Nop, modifiers .. " must consume mouse presses")
	end
end

print("WezTerm link routing passed")
