local workspaceGridMenuBarReveal = {}

local cursorReturnDelaySeconds = 0.12
local menuBarVisibleDurationSeconds = 1
local cursorPositionBeforeReveal = nil
local menuBarRevealPosition = nil
local cursorReturnTimer = nil
local menuBarHideTimer = nil

local function stopTimer(timer)
	if timer then
		timer:stop()
	end
end

local function pointsAreEqual(firstPoint, secondPoint)
	return firstPoint.x == secondPoint.x and firstPoint.y == secondPoint.y
end

local function restoreCursorIfUnmoved()
	local currentCursorPosition = hs.mouse.absolutePosition()
	if
		cursorPositionBeforeReveal
		and menuBarRevealPosition
		and pointsAreEqual(currentCursorPosition, menuBarRevealPosition)
	then
		hs.mouse.absolutePosition(cursorPositionBeforeReveal)
	end
	cursorPositionBeforeReveal = nil
	menuBarRevealPosition = nil
	cursorReturnTimer = nil
end

local function hideMenuBar()
	local currentCursorPosition = hs.mouse.absolutePosition()
	hs.eventtap.event.newMouseEvent(hs.eventtap.event.types.mouseMoved, currentCursorPosition):post()
	menuBarHideTimer = nil
end

function workspaceGridMenuBarReveal.brieflyReveal()
	local currentScreen = hs.mouse.getCurrentScreen()
	if not currentScreen then
		return
	end

	stopTimer(cursorReturnTimer)
	stopTimer(menuBarHideTimer)

	cursorPositionBeforeReveal = cursorPositionBeforeReveal or hs.mouse.absolutePosition()
	menuBarRevealPosition = {
		x = cursorPositionBeforeReveal.x,
		y = currentScreen:fullFrame().y,
	}
	hs.eventtap.event.newMouseEvent(hs.eventtap.event.types.mouseMoved, menuBarRevealPosition):post()
	cursorReturnTimer = hs.timer.doAfter(cursorReturnDelaySeconds, restoreCursorIfUnmoved)
	menuBarHideTimer = hs.timer.doAfter(menuBarVisibleDurationSeconds, hideMenuBar)
end

function workspaceGridMenuBarReveal.cancel()
	stopTimer(cursorReturnTimer)
	stopTimer(menuBarHideTimer)
	restoreCursorIfUnmoved()
	hideMenuBar()
end

return workspaceGridMenuBarReveal
