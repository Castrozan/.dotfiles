local windowServerOnScreenWindows = {}

local includeWindowsBelowTheDock = false

function windowServerOnScreenWindows.ownerNameByWindowId()
	local ownerNameByWindowId = {}
	for _, windowServerEntry in ipairs(hs.window.list(includeWindowsBelowTheDock)) do
		ownerNameByWindowId[windowServerEntry.kCGWindowNumber] = windowServerEntry.kCGWindowOwnerName or ""
	end
	return ownerNameByWindowId
end

return windowServerOnScreenWindows
