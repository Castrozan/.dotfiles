local chromeProfileWindow = {}

local personalProfileWindowTitleSuffixPattern = " %- Google Chrome %- Lucas$"
local workProfileWindowTitleDisambiguatedInfixPattern = " %- Google Chrome %- Lucas %("

function chromeProfileWindow.windowBelongsToPersonalProfile(window)
	local windowTitle = window:title()
	return windowTitle ~= nil and windowTitle:match(personalProfileWindowTitleSuffixPattern) ~= nil
end

function chromeProfileWindow.windowBelongsToWorkProfile(window)
	local windowTitle = window:title()
	return windowTitle ~= nil and windowTitle:match(workProfileWindowTitleDisambiguatedInfixPattern) ~= nil
end

return chromeProfileWindow
