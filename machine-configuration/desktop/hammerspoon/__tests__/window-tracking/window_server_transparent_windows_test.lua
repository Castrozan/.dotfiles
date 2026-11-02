local moduleDirectory = arg[0]:gsub("__tests__/.*$", "")
dofile(moduleDirectory .. "__tests__/hammerspoon_module_paths.lua")(moduleDirectory)

hs = {
	window = {
		list = function(includeWindowsBelowTheDock)
			assert(includeWindowsBelowTheDock == false)
			return {
				{ kCGWindowNumber = 8381, kCGWindowOwnerName = "Hex", kCGWindowAlpha = 0, kCGWindowLayer = 25 },
				{ kCGWindowNumber = 8382, kCGWindowOwnerName = "Hex", kCGWindowAlpha = 1, kCGWindowLayer = 0 },
				{ kCGWindowNumber = 128, kCGWindowOwnerName = "WezTerm", kCGWindowAlpha = 1 },
				{ kCGWindowNumber = 129, kCGWindowOwnerName = "Dialog", kCGWindowAlpha = 0.5 },
				{ kCGWindowNumber = 130, kCGWindowOwnerName = "Unknown opacity" },
				{ kCGWindowNumber = 8383, kCGWindowOwnerName = "Hex", kCGWindowAlpha = 1, kCGWindowLayer = 25 },
				{ kCGWindowNumber = 131, kCGWindowOwnerName = "Utility", kCGWindowAlpha = 1, kCGWindowLayer = 19 },
			}
		end,
	},
}

local ownerNames = require("window_server_on_screen_windows").ownerNameByWindowId()
assert(ownerNames[8381] == nil, "Hex's fully transparent dictation HUD must be excluded")
assert(ownerNames[8382] == "Hex", "Hex's visible Settings window must remain available")
assert(ownerNames[128] == "WezTerm", "normal windows must remain available")
assert(ownerNames[129] == "Dialog", "partially transparent windows must remain available")
assert(ownerNames[130] == "Unknown opacity", "windows without opacity metadata must remain available")
assert(ownerNames[8383] == nil, "Hex's visible recording HUD must be excluded")
assert(ownerNames[131] == "Utility", "utility windows below the status level must remain available")
print("PASS: window enumeration excludes transparent windows and status overlays")
