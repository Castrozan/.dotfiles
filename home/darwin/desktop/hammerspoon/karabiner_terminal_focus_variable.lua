local karabinerTerminalFocusVariable = {}

local karabinerCliPath = "/Library/Application Support/org.pqrs/Karabiner-Elements/bin/karabiner_cli"
local nonTerminalApplicationIsFrontmostVariableName = "non_terminal_application_is_frontmost"
local periodicReassertIntervalSeconds = 5

local terminalBundleIdentifiers = {
	["com.github.wez.wezterm"] = true,
	["net.kovidgoyal.kitty"] = true,
	["com.apple.Terminal"] = true,
	["com.googlecode.iterm2"] = true,
}

local function frontmostApplicationIsTerminal()
	local frontmostApplication = hs.application.frontmostApplication()
	if not frontmostApplication then
		return false
	end
	local bundleIdentifier = frontmostApplication:bundleID()
	return bundleIdentifier ~= nil and terminalBundleIdentifiers[bundleIdentifier] == true
end

local function setNonTerminalApplicationIsFrontmostKarabinerVariable()
	local nonTerminalApplicationIsFrontmost = frontmostApplicationIsTerminal() and 0 or 1
	hs.task
		.new(karabinerCliPath, nil, {
			"--set-variables",
			string.format(
				'{"%s":%d}',
				nonTerminalApplicationIsFrontmostVariableName,
				nonTerminalApplicationIsFrontmost
			),
		})
		:start()
end

local frontmostApplicationWatcher
local periodicReassertTimer

function karabinerTerminalFocusVariable.start()
	setNonTerminalApplicationIsFrontmostKarabinerVariable()

	frontmostApplicationWatcher = hs.application.watcher.new(function(_, eventType)
		if eventType == hs.application.watcher.activated then
			setNonTerminalApplicationIsFrontmostKarabinerVariable()
		end
	end)
	frontmostApplicationWatcher:start()

	periodicReassertTimer =
		hs.timer.doEvery(periodicReassertIntervalSeconds, setNonTerminalApplicationIsFrontmostKarabinerVariable)
end

return karabinerTerminalFocusVariable
