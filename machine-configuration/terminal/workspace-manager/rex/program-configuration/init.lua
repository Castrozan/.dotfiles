local prefix = "ctrl+b"
local terminal = "com.superlogical.terminal"
local login_shell = "/run/current-system/sw/bin/bash"

local function bind_prefixed(keys, action, args)
	if type(keys) == "string" then
		keys = { keys }
	end
	for _, key in ipairs(keys) do
		rex.bind(prefix .. ">" .. key, action, args)
	end
end

local function foreground_process(block_id)
	if not block_id then
		return nil
	end
	local process = rex.block.call(terminal, "process", { block_id = block_id })
	return process and (process.foreground or process.child)
end

rex.action({
	name = "select_session_by_position",
	title = "Go to Session by Position",
	category = "Session",
	args = { position = "integer" },
	run = function(ctx, args)
		local listing = rex.call("session.list")
		local session = listing and listing.sessions and listing.sessions[args.position]
		if session then
			rex.client.queue("session.select", { session_id = session.session_id })
		end
	end,
})

rex.action({
	name = "select_tab_by_position",
	title = "Go to Tab by Position",
	category = "Tab",
	args = { position = "integer" },
	run = function(ctx, args)
		local view = rex.session.view({})
		local window = view and view.windows and view.windows[args.position]
		if window then
			rex.client.queue("session.select", { session_id = ctx.session_id, window_id = window.window_id })
		end
	end,
})

rex.action({
	name = "open_command_pane",
	title = "Open Command Pane",
	category = "Pane",
	args = { command = "string" },
	run = function(ctx, args)
		local origin_process = foreground_process(ctx.block_id)
		local split = rex.session.new_split({
			anchor_id = ctx.block_id,
			direction = "horizontal",
			side = "after",
			focus = true,
			layout = rex.layout.block({
				flavor = terminal .. ".shell",
				options = {
					shell = login_shell,
					command = { login_shell, "-c", args.command },
					cwd = origin_process and origin_process.cwd or nil,
				},
			}),
		})
		if split then
			rex.session.zoom_block({ block_id = split.block_ids[1], zoom = true })
		end
	end,
})

rex.action({
	name = "step_tab_unless_nvim",
	title = "Step Tab Unless Neovim Has Focus",
	category = "Tab",
	args = { key = "string", tab_action = "string" },
	run = function(ctx, args)
		local process = foreground_process(ctx.block_id)
		if process and process.name == "nvim" then
			rex.client.queue("pane.send_key", { key = args.key })
		else
			rex.client.queue(args.tab_action)
		end
	end,
})

rex.action({
	name = "write_key_sequence",
	title = "Write Key Sequence",
	category = "Pane",
	args = { sequence = "string" },
	run = function(ctx, args)
		if ctx.block_id then
			rex.block.call(terminal, "write", { block_id = ctx.block_id, data = args.sequence })
		end
	end,
})

local function bind_tab_step(key, tab_action)
	rex.bind(key, "step_tab_unless_nvim", { key = key, tab_action = tab_action })
end

bind_prefixed("a", "client.config.reload")
bind_prefixed("d", "client.visibility.toggle")
bind_prefixed("w", "client.settings")

bind_prefixed("c", "client.tab.new")
bind_prefixed("r", "client.tab.rename")
rex.bind("ctrl+shift+w", "client.tab.close")
rex.bind("shift+cmd+r", "client.config.reload")
bind_prefixed("shift+7", "client.tab.close")
bind_prefixed("pageup", "client.tab.previous")
bind_prefixed("pagedown", "client.tab.next")
bind_tab_step("ctrl+pageup", "client.tab.previous")
bind_tab_step("ctrl+pagedown", "client.tab.next")
rex.bind("ctrl+shift+pageup", "client.tab.move.backward")
rex.bind("ctrl+shift+pagedown", "client.tab.move.forward")
local shifted_digits_with_tmux_meaning = { [5] = true, [7] = true }
for position = 1, 9 do
	bind_prefixed(tostring(position), "select_tab_by_position", { position = position })
	if not shifted_digits_with_tmux_meaning[position] then
		bind_prefixed("shift+" .. position, "select_session_by_position", { position = position })
	end
end

bind_prefixed("shift+n", "session.new")
bind_prefixed("shift+w", "session.rename")
bind_prefixed("shift+d", "session.close")
bind_prefixed("g", "session.switch")
bind_prefixed({ "s", "ctrl+s" }, "session.switch")

bind_prefixed("x", "client.close")
bind_prefixed("z", "pane.zoom")
bind_prefixed("left", "pane.focus.left")
bind_prefixed("down", "pane.focus.down")
bind_prefixed("up", "pane.focus.up")
bind_prefixed("right", "pane.focus.right")
bind_prefixed({ "o", "ctrl+o" }, "pane.focus_next")
bind_prefixed("shift+o", "pane.focus_previous")
bind_prefixed("shift+5", "pane.split.right")
bind_prefixed("shift+'", "pane.split.down")
bind_prefixed("[", "pane.copy_mode.enter")
bind_prefixed("ctrl+c", "pane.move_to_new_tab")
bind_prefixed("shift+b", "client.sidebar.toggle")
bind_prefixed("shift+/", "client.palette.toggle")
bind_prefixed("shift+p", "pane.rename")
bind_prefixed("shift+s", "session.new")
bind_prefixed("shift+left", "client.tab.move.backward")
bind_prefixed("shift+right", "client.tab.move.forward")
for key, direction in pairs({ h = "left", j = "down", k = "up", l = "right" }) do
	bind_prefixed("shift+" .. key, "pane.move", { direction = direction })
end

rex.mode("resize", { exclusive = true })
bind_prefixed("shift+r", "client.mode.enter", { name = "resize" })
for key, direction in pairs({
	left = "left",
	down = "down",
	up = "up",
	right = "right",
	h = "left",
	j = "down",
	k = "up",
	l = "right",
}) do
	rex.bind("resize/" .. key, "pane.resize", { direction = direction })
end
rex.bind("resize/=", "pane.balance")
rex.bind("resize/enter", "client.mode.exit")

for key, command in pairs({
	i = "lazygit",
	["shift+i"] = "review-changes",
	b = "btop",
	e = "code . -n",
	v = "nvim .",
	t = "claude-show-session | LESS='-R +G' less",
}) do
	bind_prefixed(key, "open_command_pane", { command = command })
end

rex.bind("ctrl+g", "pane.send_key", { key = "ctrl+b" })

for key, sequence in pairs({
	["shift+enter"] = "\27[13;2u",
	["ctrl+enter"] = "\27[13;5u",
	["alt+enter"] = "\27[13;3u",
	["ctrl+shift+up"] = "\27[1;6A",
	["ctrl+shift+down"] = "\27[1;6B",
}) do
	rex.bind(key, "write_key_sequence", { sequence = sequence })
end
