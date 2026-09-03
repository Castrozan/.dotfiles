local moduleDirectory = arg[0]:gsub("__tests__/[^/]*$", "")
package.path = moduleDirectory .. "?.lua;" .. package.path

local timers = {}
local applicationTimeouts = {}
local menuBarTimeouts = {}
local selectedChildrenAssignments = {}
local performedActions = {}
local frontmostApplication = {}
local menuBarSelectionIsSettable = true
local menuBarSelectionSucceeds = true

local function makeTimer(delaySeconds, callback)
	local timer = { delaySeconds = delaySeconds, stopped = false }
	function timer:stop()
		self.stopped = true
	end
	function timer:fire()
		if not self.stopped then
			self.stopped = true
			callback()
		end
	end
	table.insert(timers, timer)
	return timer
end

local firstMenuItem = {}
local selectedChildren = {}
local menuBar = {}

function menuBar:attributeValue(attributeName)
	if attributeName == "AXRole" then
		return "AXMenuBar"
	end
	if attributeName == "AXChildren" then
		return { firstMenuItem }
	end
	if attributeName == "AXSelectedChildren" then
		return selectedChildren
	end
end

function menuBar:isAttributeSettable(attributeName)
	return attributeName == "AXSelectedChildren" and menuBarSelectionIsSettable
end

function menuBar:actionNames()
	return { "AXCancel" }
end

function menuBar:setAttributeValue(attributeName, value)
	table.insert(selectedChildrenAssignments, { attributeName = attributeName, value = value })
	if not menuBarSelectionSucceeds then
		return nil, "selection rejected"
	end
	selectedChildren = value
	return self
end

function menuBar:setTimeout(timeoutSeconds)
	table.insert(menuBarTimeouts, timeoutSeconds)
	return self
end

function menuBar:isValid()
	return true
end

function menuBar:performAction(actionName)
	table.insert(performedActions, actionName)
	selectedChildren = {}
	return self
end

local nonMenuChild = {}
function nonMenuChild:attributeValue(attributeName)
	if attributeName == "AXRole" then
		return "AXWindow"
	end
end

local applicationElement = {}
function applicationElement:attributeValue(attributeName)
	if attributeName == "AXChildren" then
		return { nonMenuChild, menuBar }
	end
end

function applicationElement:setTimeout(timeoutSeconds)
	table.insert(applicationTimeouts, timeoutSeconds)
	return self
end

hs = {
	application = {
		frontmostApplication = function()
			return frontmostApplication
		end,
	},
	axuielement = {
		applicationElement = function(application)
			if application then
				return applicationElement
			end
		end,
	},
	timer = {
		doAfter = makeTimer,
	},
}

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print(string.format("PASS: %s", description))
	end
end

local menuBarReveal = require("workspace_grid_menu_bar_reveal")

menuBarReveal.brieflyReveal()
expectEqual("reveal waits for the focus change to settle", 0, timers[1].delaySeconds)
expectEqual("reveal does not select the old application menu", 0, #selectedChildrenAssignments)

timers[1]:fire()
expectEqual("the application query has a bounded timeout", 0.1, applicationTimeouts[1])
expectEqual("the menu bar query has a bounded timeout", 0.1, menuBarTimeouts[1])
expectEqual("the menu bar selection is changed", "AXSelectedChildren", selectedChildrenAssignments[1].attributeName)
expectEqual("the first menu item is selected", firstMenuItem, selectedChildrenAssignments[1].value[1])
expectEqual("the menu bar remains visible briefly", 1, timers[2].delaySeconds)

timers[2]:fire()
expectEqual("hiding cancels the menu bar selection", "AXCancel", performedActions[1])
expectEqual("hiding clears the selected menu item", 0, #selectedChildren)

menuBarReveal.brieflyReveal()
timers[3]:fire()
menuBarReveal.brieflyReveal()
expectEqual("a repeated reveal cancels the previous hide timer", true, timers[4].stopped)
expectEqual("a repeated reveal cancels the previous selection", "AXCancel", performedActions[2])
expectEqual("a repeated reveal schedules against the new frontmost application", 0, timers[5].delaySeconds)

timers[5]:fire()
menuBarReveal.cancel()
expectEqual("cancelling stops the pending hide timer", true, timers[6].stopped)
expectEqual("cancelling clears the active selection", "AXCancel", performedActions[3])

menuBarSelectionIsSettable = false
menuBarReveal.brieflyReveal()
timers[7]:fire()
expectEqual("an unsupported application does not schedule a hide", 7, #timers)
expectEqual("an unsupported application does not change selection", 3, #selectedChildrenAssignments)

menuBarSelectionIsSettable = true
menuBarSelectionSucceeds = false
menuBarReveal.brieflyReveal()
timers[8]:fire()
expectEqual("a rejected selection does not schedule a hide", 8, #timers)

os.exit(failureCount == 0 and 0 or 1)
