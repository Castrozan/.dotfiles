local workspaceGridTwoWindowTilingHotkeys = {}

local function setEnabled(hotkey, enabled)
	if enabled then
		hotkey:enable()
	else
		hotkey:disable()
	end
end

function workspaceGridTwoWindowTilingHotkeys.install(workspaceGrid)
	local leftHotkey = hs.hotkey.new({ "cmd" }, "left", function()
		workspaceGrid.focusLeftTiledWindow()
	end)
	local rightHotkey = hs.hotkey.new({ "cmd" }, "right", function()
		workspaceGrid.focusRightTiledWindow()
	end)
	local hotkeys = { leftHotkey, rightHotkey }
	local function synchronizeWithTilingState()
		for _, hotkey in ipairs(hotkeys) do
			setEnabled(hotkey, workspaceGrid.twoWindowTilingIsActive())
		end
	end
	workspaceGrid.observeWorkspaceLayoutChanges(synchronizeWithTilingState)
	synchronizeWithTilingState()
	return hotkeys
end

return workspaceGridTwoWindowTilingHotkeys
