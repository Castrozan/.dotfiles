local karabinerApplicationFocusVariables = {}

local karabinerCliPath = "/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli"
local periodicReassertIntervalSeconds = 5

local terminalBundleIdentifiers = {
	["com.github.wez.wezterm"] = true,
	["net.kovidgoyal.kitty"] = true,
	["com.apple.Terminal"] = true,
	["com.googlecode.iterm2"] = true,
}
local braveBrowserBundleIdentifier = "com.brave.Browser"

local function currentFrontmostBundleIdentifier()
	local frontmostApplication = hs.application.frontmostApplication()
	if not frontmostApplication then
		return nil
	end
	return frontmostApplication:bundleID()
end

local function setKarabinerApplicationFocusVariables()
	local bundleIdentifier = currentFrontmostBundleIdentifier()
	local frontmostIsTerminal = bundleIdentifier ~= nil and terminalBundleIdentifiers[bundleIdentifier] == true
	local frontmostIsBraveBrowser = bundleIdentifier == braveBrowserBundleIdentifier

	local applicationFocusVariablesJson = string.format(
		'{"terminal_application_is_frontmost":%d,'
			.. '"non_terminal_application_is_frontmost":%d,'
			.. '"brave_browser_is_frontmost":%d}',
		frontmostIsTerminal and 1 or 0,
		frontmostIsTerminal and 0 or 1,
		frontmostIsBraveBrowser and 1 or 0
	)

	hs.task.new(karabinerCliPath, nil, { "--set-variables", applicationFocusVariablesJson }):start()
end

local frontmostApplicationWatcher
local periodicReassertTimer

function karabinerApplicationFocusVariables.start()
	setKarabinerApplicationFocusVariables()

	frontmostApplicationWatcher = hs.application.watcher.new(function(_, eventType)
		if eventType == hs.application.watcher.activated then
			setKarabinerApplicationFocusVariables()
		end
	end)
	frontmostApplicationWatcher:start()

	periodicReassertTimer = hs.timer.doEvery(periodicReassertIntervalSeconds, setKarabinerApplicationFocusVariables)
end

return karabinerApplicationFocusVariables
