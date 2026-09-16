return function(moduleDirectory)
	for _, sourceDirectory in ipairs({
		"",
		"workspaces/",
		"window-tiling/",
		"menu-bar/",
		"application-summoning/",
		"window-server/",
		"input/",
		"__tests__/support/",
	}) do
		package.path = moduleDirectory .. sourceDirectory .. "?.lua;" .. package.path
	end
end
