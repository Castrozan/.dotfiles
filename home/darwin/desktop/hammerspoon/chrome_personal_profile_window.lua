local chromePersonalProfileWindow = {}

local personalProfileWindowTitleSuffixPattern = " %- Google Chrome %- Lucas$"

function chromePersonalProfileWindow.windowBelongsToPersonalProfile(window)
	local windowTitle = window:title()
	return windowTitle ~= nil and windowTitle:match(personalProfileWindowTitleSuffixPattern) ~= nil
end

return chromePersonalProfileWindow
