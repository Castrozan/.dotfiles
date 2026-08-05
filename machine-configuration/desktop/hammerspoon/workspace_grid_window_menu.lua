local workspaceGridWindowMenu = {}

local maximumWindowTitleCharacterCount = 60
local applicationIconEdgeLength = 16

local applicationIconsByBundleIdentifier = {}

local function applicationIcon(applicationBundleIdentifier)
	if applicationBundleIdentifier == nil or applicationBundleIdentifier == "" then
		return nil
	end
	local cachedIcon = applicationIconsByBundleIdentifier[applicationBundleIdentifier]
	if cachedIcon ~= nil then
		return cachedIcon or nil
	end
	local icon = hs.image.imageFromAppBundle(applicationBundleIdentifier)
	if icon then
		icon = icon:setSize({ w = applicationIconEdgeLength, h = applicationIconEdgeLength })
	end
	applicationIconsByBundleIdentifier[applicationBundleIdentifier] = icon or false
	return icon
end

local function shortenedWindowTitle(windowTitle)
	local characterCount = utf8.len(windowTitle)
	if characterCount == nil or characterCount <= maximumWindowTitleCharacterCount then
		return windowTitle
	end
	local byteOffsetPastLastKeptCharacter = utf8.offset(windowTitle, maximumWindowTitleCharacterCount + 1)
	return windowTitle:sub(1, byteOffsetPastLastKeptCharacter - 1) .. "…"
end

local function menuItemTitleForDescriptor(windowDescriptor)
	local windowTitle = windowDescriptor["window-title"] or ""
	if windowTitle ~= "" then
		return shortenedWindowTitle(windowTitle)
	end
	local applicationName = windowDescriptor["app-name"] or ""
	if applicationName ~= "" then
		return applicationName
	end
	return "Untitled window"
end

local function descriptorSortsBefore(leftDescriptor, rightDescriptor)
	if leftDescriptor["app-name"] ~= rightDescriptor["app-name"] then
		return leftDescriptor["app-name"] < rightDescriptor["app-name"]
	end
	if leftDescriptor["window-title"] ~= rightDescriptor["window-title"] then
		return leftDescriptor["window-title"] < rightDescriptor["window-title"]
	end
	return leftDescriptor["window-id"] < rightDescriptor["window-id"]
end

local function descriptorsInStableClickOrder(windowDescriptors)
	local orderedDescriptors = {}
	for _, windowDescriptor in ipairs(windowDescriptors) do
		table.insert(orderedDescriptors, windowDescriptor)
	end
	table.sort(orderedDescriptors, descriptorSortsBefore)
	return orderedDescriptors
end

local function workspaceNumbersWithCurrentFirst(descriptorsByWorkspaceNumber, currentWorkspaceNumber)
	local otherWorkspaceNumbers = {}
	for workspaceNumber in pairs(descriptorsByWorkspaceNumber) do
		if workspaceNumber ~= currentWorkspaceNumber then
			table.insert(otherWorkspaceNumbers, workspaceNumber)
		end
	end
	table.sort(otherWorkspaceNumbers)
	local orderedWorkspaceNumbers = {}
	if descriptorsByWorkspaceNumber[currentWorkspaceNumber] ~= nil then
		table.insert(orderedWorkspaceNumbers, currentWorkspaceNumber)
	end
	for _, workspaceNumber in ipairs(otherWorkspaceNumbers) do
		table.insert(orderedWorkspaceNumbers, workspaceNumber)
	end
	return orderedWorkspaceNumbers
end

local function workspaceHeadingTitle(workspaceNumber, currentWorkspaceNumber)
	if workspaceNumber == currentWorkspaceNumber then
		return string.format("Workspace %d (current)", workspaceNumber)
	end
	return string.format("Workspace %d", workspaceNumber)
end

function workspaceGridWindowMenu.menuItemsForSnapshot(windowSnapshot, currentWorkspaceNumber, revealWindowById)
	local descriptorsByWorkspaceNumber = windowSnapshot.descriptorsByWorkspaceNumber or {}
	local orderedWorkspaceNumbers =
		workspaceNumbersWithCurrentFirst(descriptorsByWorkspaceNumber, currentWorkspaceNumber)
	if #orderedWorkspaceNumbers == 0 then
		return { { title = "No windows", disabled = true } }
	end
	local menuItems = {}
	for _, workspaceNumber in ipairs(orderedWorkspaceNumbers) do
		if #menuItems > 0 then
			table.insert(menuItems, { title = "-" })
		end
		table.insert(menuItems, {
			title = workspaceHeadingTitle(workspaceNumber, currentWorkspaceNumber),
			disabled = true,
		})
		for _, windowDescriptor in ipairs(descriptorsInStableClickOrder(descriptorsByWorkspaceNumber[workspaceNumber])) do
			local windowId = windowDescriptor["window-id"]
			table.insert(menuItems, {
				title = menuItemTitleForDescriptor(windowDescriptor),
				image = applicationIcon(windowDescriptor["app-bundle-id"]),
				indent = 1,
				checked = windowId == windowSnapshot.focusedWindowId,
				fn = function()
					revealWindowById(windowId)
				end,
			})
		end
	end
	return menuItems
end

function workspaceGridWindowMenu.buildMenuItemBuilder(dependencies)
	return function()
		return workspaceGridWindowMenu.menuItemsForSnapshot(
			dependencies.snapshotForImmediateUse(),
			dependencies.currentWorkspaceNumber(),
			dependencies.revealWindowById
		)
	end
end

return workspaceGridWindowMenu
