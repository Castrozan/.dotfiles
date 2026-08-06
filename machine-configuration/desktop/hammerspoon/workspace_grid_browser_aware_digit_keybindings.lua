local workspaceGridBrowserAwareDigitKeybindings = {}

local browserBundleIdentifiers = {
	["com.google.Chrome"] = true,
	["com.brave.Browser"] = true,
}

local function isPlainCommandDigitChord(eventFlags, keyCode, workspaceColumnByKeyCode)
	if not eventFlags or not eventFlags.cmd or eventFlags.alt or eventFlags.ctrl or eventFlags.shift then
		return false
	end
	return workspaceColumnByKeyCode[keyCode] ~= nil
end

function workspaceGridBrowserAwareDigitKeybindings.buildRoutingDecision(
	eventFlags,
	keyCode,
	frontmostApplicationBundleIdentifier,
	workspaceColumnByKeyCode
)
	if not isPlainCommandDigitChord(eventFlags, keyCode, workspaceColumnByKeyCode) then
		return nil
	end
	if browserBundleIdentifiers[frontmostApplicationBundleIdentifier] then
		return nil
	end
	return workspaceColumnByKeyCode[keyCode]
end

local function currentFrontmostApplicationBundleIdentifier()
	local frontmostApplication = hs.application.frontmostApplication()
	if not frontmostApplication then
		return nil
	end
	return frontmostApplication:bundleID()
end

function workspaceGridBrowserAwareDigitKeybindings.install(dependencies)
	local keyDownEventTap = hs.eventtap.new({ hs.eventtap.event.types.keyDown }, function(event)
		local workspaceColumnNumber = workspaceGridBrowserAwareDigitKeybindings.buildRoutingDecision(
			event:getFlags(),
			event:getKeyCode(),
			currentFrontmostApplicationBundleIdentifier(),
			dependencies.workspaceColumnByKeyCode
		)
		if workspaceColumnNumber == nil then
			return nil
		end
		dependencies.workspaceGrid.switchToWorkspace(workspaceColumnNumber)
		return true
	end)
	keyDownEventTap:start()
	return keyDownEventTap
end

return workspaceGridBrowserAwareDigitKeybindings
