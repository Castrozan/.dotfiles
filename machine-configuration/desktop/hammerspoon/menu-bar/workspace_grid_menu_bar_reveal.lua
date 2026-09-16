local workspaceGridMenuBarReveal = {}

local accessibilityTimeoutSeconds = 0.1
local menuBarVisibleDurationSeconds = 1
local pendingRevealTimer = nil
local pendingHideTimer = nil
local selectedMenuBar = nil

local function stopTimer(timer)
	if timer then
		timer:stop()
	end
end

local function supportsAction(accessibilityElement, expectedActionName)
	for _, actionName in ipairs(accessibilityElement:actionNames() or {}) do
		if actionName == expectedActionName then
			return true
		end
	end
	return false
end

local function cancelSelectedMenuBar()
	if selectedMenuBar and selectedMenuBar:isValid() then
		selectedMenuBar:performAction("AXCancel")
	end
	selectedMenuBar = nil
end

local function frontmostApplicationMenuBar()
	local frontmostApplication = hs.application.frontmostApplication()
	if not frontmostApplication then
		return nil
	end
	local applicationElement = hs.axuielement.applicationElement(frontmostApplication)
	if not applicationElement then
		return nil
	end
	applicationElement:setTimeout(accessibilityTimeoutSeconds)
	for _, childElement in ipairs(applicationElement:attributeValue("AXChildren") or {}) do
		if childElement:attributeValue("AXRole") == "AXMenuBar" then
			childElement:setTimeout(accessibilityTimeoutSeconds)
			return childElement
		end
	end
	return nil
end

local function revealFrontmostApplicationMenuBar()
	pendingRevealTimer = nil
	local menuBar = frontmostApplicationMenuBar()
	if
		not menuBar
		or not menuBar:isAttributeSettable("AXSelectedChildren")
		or not supportsAction(menuBar, "AXCancel")
	then
		return
	end
	local menuBarChildren = menuBar:attributeValue("AXChildren") or {}
	if not menuBarChildren[1] then
		return
	end
	if not menuBar:setAttributeValue("AXSelectedChildren", { menuBarChildren[1] }) then
		return
	end
	local selectedChildren = menuBar:attributeValue("AXSelectedChildren") or {}
	if not selectedChildren[1] then
		return
	end
	selectedMenuBar = menuBar
	pendingHideTimer = hs.timer.doAfter(menuBarVisibleDurationSeconds, function()
		pendingHideTimer = nil
		cancelSelectedMenuBar()
	end)
end

function workspaceGridMenuBarReveal.cancel()
	stopTimer(pendingRevealTimer)
	stopTimer(pendingHideTimer)
	pendingRevealTimer = nil
	pendingHideTimer = nil
	cancelSelectedMenuBar()
end

function workspaceGridMenuBarReveal.brieflyReveal()
	workspaceGridMenuBarReveal.cancel()
	pendingRevealTimer = hs.timer.doAfter(0, revealFrontmostApplicationMenuBar)
end

return workspaceGridMenuBarReveal
