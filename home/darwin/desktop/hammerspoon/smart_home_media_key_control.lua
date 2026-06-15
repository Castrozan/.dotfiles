local smartHomeMediaKeyControl = {}

local homeAssistantBinaryDirectory = "@USER_BIN_PATH@"

local mediaKeyToHomeAssistantCommand = {
	SOUND_UP = { binaryName = "ha-light-scene-cycle", arguments = {} },
	SOUND_DOWN = { binaryName = "ha-ac-toggle", arguments = {} },
	MUTE = { binaryName = "ha-light", arguments = { "off", "all" } },
}

local function runHomeAssistantCommand(command)
	hs.task.new(homeAssistantBinaryDirectory .. "/" .. command.binaryName, nil, command.arguments):start()
end

local function handleSystemDefinedEvent(event)
	local systemKeyData = event:systemKey()
	if not systemKeyData then
		return false
	end
	local command = mediaKeyToHomeAssistantCommand[systemKeyData.key]
	if not command then
		return false
	end
	local pressedModifiers = hs.eventtap.checkKeyboardModifiers()
	if not pressedModifiers.ctrl or pressedModifiers.cmd or pressedModifiers.alt or pressedModifiers.shift then
		return false
	end
	if systemKeyData.down and not systemKeyData["repeat"] then
		runHomeAssistantCommand(command)
	end
	return true
end

function smartHomeMediaKeyControl.start()
	smartHomeMediaKeyControl.eventTap =
		hs.eventtap.new({ hs.eventtap.event.types.systemDefined }, handleSystemDefinedEvent)
	smartHomeMediaKeyControl.eventTap:start()
end

return smartHomeMediaKeyControl
