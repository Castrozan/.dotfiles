local environment = {}

local failureCount = 0

function environment.pendingTimers()
	local pending = {}
	for _, timer in ipairs(environment.timers) do
		if not timer.stopped then
			table.insert(pending, timer)
		end
	end
	return pending
end

function environment.runningCommands()
	local running = {}
	for _, command in ipairs(environment.launchedCommands) do
		if not command.exited then
			table.insert(running, command)
		end
	end
	return running
end

function environment.forcedVisibleDisplayCount()
	local count = 0
	for _ in pairs(environment.forcedVisibleByDisplayId) do
		count = count + 1
	end
	return count
end

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
	table.insert(environment.timers, timer)
	return timer
end

local function makeCommandTask(launchPath, onExit, arguments)
	local task = {
		launchPath = launchPath,
		arguments = arguments,
		displayId = tonumber(arguments[5]),
		visible = arguments[6] == "true",
		exited = false,
		waitedSynchronously = false,
	}
	function task:start()
		if not environment.commandStarts(self) then
			return false
		end
		table.insert(environment.launchedCommands, self)
		environment.highestConcurrentCommandCount =
			math.max(environment.highestConcurrentCommandCount, #environment.runningCommands())
		return self
	end
	function task:applyToWindowServer()
		environment.forcedVisibleByDisplayId[self.displayId] = self.visible or nil
	end
	function task:exit(exitCode, standardOutput, standardError)
		self.exited = true
		if exitCode == 0 and standardOutput == "0\n" then
			self:applyToWindowServer()
		end
		if onExit then
			onExit(exitCode, standardOutput, standardError)
		end
	end
	function task:setCallback(replacementOnExit)
		onExit = replacementOnExit
		return self
	end
	function task:waitUntilExit()
		self.waitedSynchronously = true
		if not self.exited then
			self:exit(0, "0\n", "")
		end
		return self
	end
	return task
end

local function makeScreen(displayId)
	if displayId then
		return {
			id = function()
				return displayId
			end,
		}
	end
end

function environment.loadFreshMenuBarReveal()
	environment.timers = {}
	environment.launchedCommands = {}
	environment.forcedVisibleByDisplayId = {}
	environment.reportedFailures = {}
	environment.focusedDisplayId = 2
	environment.mainDisplayId = 1
	environment.highestConcurrentCommandCount = 0
	environment.commandStarts = function()
		return true
	end
	hs = {
		window = {
			focusedWindow = function()
				if environment.focusedDisplayId then
					return {
						screen = function()
							return makeScreen(environment.focusedDisplayId)
						end,
					}
				end
			end,
		},
		screen = {
			mainScreen = function()
				return makeScreen(environment.mainDisplayId)
			end,
		},
		application = {
			frontmostApplication = function()
				error("revealing the bar must not select an application menu")
			end,
		},
		osascript = {
			javascript = function()
				error("JavaScript must never run inside the Hammerspoon process")
			end,
		},
		timer = { doAfter = makeTimer },
		task = { new = makeCommandTask },
		printf = function(...)
			table.insert(environment.reportedFailures, string.format(...))
		end,
	}
	package.loaded["workspace_grid_menu_bar_reveal"] = nil
	return require("workspace_grid_menu_bar_reveal")
end

local function firePendingTimerWithDelay(delaySeconds)
	for _, timer in ipairs(environment.pendingTimers()) do
		if timer.delaySeconds == delaySeconds then
			timer:fire()
			return
		end
	end
	error("no pending timer with delay " .. delaySeconds)
end

function environment.settleFocus()
	firePendingTimerWithDelay(0)
end

function environment.finishVisibleDuration()
	firePendingTimerWithDelay(1)
end

function environment.exitRunningCommand(exitCode, standardOutput, standardError)
	environment.runningCommands()[1]:exit(exitCode or 0, standardOutput or "0\n", standardError or "")
end

function environment.describeCommand(command)
	if not command then
		return "none"
	end
	return (command.visible and "show " or "hide ") .. command.displayId
end

function environment.expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print("PASS: " .. description)
	end
end

function environment.exitWithAccumulatedResult()
	os.exit(failureCount == 0 and 0 or 1)
end

return environment
