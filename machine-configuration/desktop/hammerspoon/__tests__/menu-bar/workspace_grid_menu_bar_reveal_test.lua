local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

local timers = {}
local tasks = {}
local activeTaskCount = 0
local maximumActiveTaskCount = 0
local focusedDisplayId = 2
local taskStartSucceeds = true
local reportedFailures = {}

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

local function makeScreen(displayId)
	return {
		id = function()
			return displayId
		end,
	}
end

hs = {
	window = {
		focusedWindow = function()
			if focusedDisplayId then
				return {
					screen = function()
						return makeScreen(focusedDisplayId)
					end,
				}
			end
		end,
	},
	screen = {
		mainScreen = function()
			return makeScreen(1)
		end,
	},
	application = {
		frontmostApplication = function()
			error("revealing the bar must not select an application menu")
		end,
	},
	timer = { doAfter = makeTimer },
	task = {
		new = function(executable, callback, arguments)
			local task = { executable = executable, arguments = arguments, terminated = false }
			function task:start()
				if not taskStartSucceeds then
					return false
				end
				activeTaskCount = activeTaskCount + 1
				maximumActiveTaskCount = math.max(maximumActiveTaskCount, activeTaskCount)
				return self
			end
			function task:terminate()
				self.terminated = true
			end
			function task:complete(exitCode)
				activeTaskCount = activeTaskCount - 1
				callback(exitCode or 0, "", "visibility unavailable")
			end
			table.insert(tasks, task)
			return task
		end,
	},
	printf = function(...)
		table.insert(reportedFailures, string.format(...))
	end,
}

local failureCount = 0
local function expectEqual(description, expectedValue, actualValue)
	if expectedValue ~= actualValue then
		failureCount = failureCount + 1
		print(
			string.format("FAIL: %s (expected %s, got %s)", description, tostring(expectedValue), tostring(actualValue))
		)
	else
		print("PASS: " .. description)
	end
end

local menuBarReveal = require("workspace_grid_menu_bar_reveal")
menuBarReveal.brieflyReveal()
expectEqual("reveal waits for workspace focus to settle", 0, timers[1].delaySeconds)
expectEqual("the old workspace is not revealed", 0, #tasks)
timers[1]:fire()
expectEqual("the focused window determines the display", "2", tasks[1].arguments[1])

menuBarReveal.brieflyReveal()
expectEqual("another reveal terminates the previous helper", true, tasks[1].terminated)
timers[2]:fire()
expectEqual("a replacement waits for the old override to be released", 1, #tasks)
focusedDisplayId = 3
menuBarReveal.brieflyReveal()
timers[3]:fire()
tasks[1]:complete(15)
expectEqual("rapid switches coalesce onto the latest display", "3", tasks[2].arguments[1])
expectEqual("cancelling a helper does not report an error", 0, #reportedFailures)
expectEqual("there is never more than one helper process", 1, maximumActiveTaskCount)
tasks[2]:complete()

focusedDisplayId = nil
menuBarReveal.brieflyReveal()
timers[4]:fire()
expectEqual("an empty workspace uses the main display", "1", tasks[3].arguments[1])
menuBarReveal.brieflyReveal()
timers[5]:fire()
menuBarReveal.cancel()
tasks[3]:complete(15)
expectEqual("shutdown discards a queued reveal", 3, #tasks)

menuBarReveal.brieflyReveal()
menuBarReveal.cancel()
timers[6]:fire()
expectEqual("cancellation before focus settles launches nothing", 3, #tasks)

taskStartSucceeds = false
menuBarReveal.brieflyReveal()
timers[7]:fire()
expectEqual("failure to start is reported", 1, #reportedFailures)
taskStartSucceeds = true
menuBarReveal.brieflyReveal()
timers[8]:fire()
tasks[5]:complete(1)
expectEqual("an unavailable visibility API is reported without selecting a menu", 2, #reportedFailures)
menuBarReveal.brieflyReveal()
timers[9]:fire()
tasks[6]:complete()
expectEqual("a failed helper does not block later reveals", 0, activeTaskCount)

os.exit(failureCount == 0 and 0 or 1)
