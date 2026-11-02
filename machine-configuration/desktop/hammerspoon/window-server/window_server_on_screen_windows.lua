local windowServerOnScreenWindows = {}

local includeWindowsBelowTheDock = false

function windowServerOnScreenWindows.ownerNameByWindowId()
	local ownerNameByWindowId = {}
	for _, windowServerEntry in ipairs(hs.window.list(includeWindowsBelowTheDock)) do
		if windowServerEntry.kCGWindowAlpha ~= 0 then
			ownerNameByWindowId[windowServerEntry.kCGWindowNumber] = windowServerEntry.kCGWindowOwnerName or ""
		end
	end
	return ownerNameByWindowId
end

return windowServerOnScreenWindows
