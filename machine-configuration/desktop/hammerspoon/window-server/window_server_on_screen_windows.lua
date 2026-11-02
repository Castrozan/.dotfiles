local windowServerOnScreenWindows = {}

local includeWindowsBelowTheDock = false
local statusWindowLevel = 25

function windowServerOnScreenWindows.ownerNameByWindowId()
	local ownerNameByWindowId = {}
	for _, windowServerEntry in ipairs(hs.window.list(includeWindowsBelowTheDock)) do
		local windowLevel = windowServerEntry.kCGWindowLayer or 0
		if windowServerEntry.kCGWindowAlpha ~= 0 and windowLevel < statusWindowLevel then
			ownerNameByWindowId[windowServerEntry.kCGWindowNumber] = windowServerEntry.kCGWindowOwnerName or ""
		end
	end
	return ownerNameByWindowId
end

return windowServerOnScreenWindows
