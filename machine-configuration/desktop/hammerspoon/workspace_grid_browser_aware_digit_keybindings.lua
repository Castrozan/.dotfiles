local workspaceGridBrowserAwareDigitKeybindings = {}

local browserBundleIdentifiers = {
	["com.google.Chrome"] = true,
	["com.brave.Browser"] = true,
}

local function isDigitChord(eventFlags, keyCode, workspaceColumnByKeyCode)
	if not eventFlags or not eventFlags.cmd or eventFlags.alt or eventFlags.ctrl then
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
	if not isDigitChord(eventFlags, keyCode, workspaceColumnByKeyCode) then
		return nil
	end
	local workspaceColumnNumber = workspaceColumnByKeyCode[keyCode]
	if browserBundleIdentifiers[frontmostApplicationBundleIdentifier] then
		if eventFlags.shift then
			return { kind = "ignore" }
		end
		return nil
	end
	if eventFlags.shift then
		return { kind = "ignore" }
	end
	return { kind = "switch", workspaceNumber = workspaceColumnNumber }
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
		local routingDecision = workspaceGridBrowserAwareDigitKeybindings.buildRoutingDecision(
			event:getFlags(),
			event:getKeyCode(),
			currentFrontmostApplicationBundleIdentifier(),
			dependencies.workspaceColumnByKeyCode
		)
		if routingDecision == nil then
			return nil
		end
		if routingDecision.kind == "ignore" then
			return true
		end
		dependencies.workspaceGrid.switchToWorkspace(routingDecision.workspaceNumber)
		return true
	end)
	keyDownEventTap:start()
	return keyDownEventTap
end

return workspaceGridBrowserAwareDigitKeybindings
