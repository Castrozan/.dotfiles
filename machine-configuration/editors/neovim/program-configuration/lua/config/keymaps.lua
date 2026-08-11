local map = vim.keymap.set

local buffer_closing = require("config.buffer_closing")
local command_line_abbreviations = require("config.command_line_abbreviations")
local file_creation = require("config.file_creation")
local file_explorer = require("config.navigation.file_explorer")
local lazyvim_defaults = require("config.lazyvim_defaults")
local pickers = require("config.navigation.pickers")
local ten_line_jumping = require("config.navigation.ten_line_jumping")
local terminal = require("config.terminal")

lazyvim_defaults.remove_window_resize_keymaps()

map({ "n", "i", "v" }, "<C-s>", "<cmd>w<cr><esc>", { desc = "Save file" })
map("n", "<C-q>", "<cmd>qa<cr>", { desc = "Quit all" })

map("n", "<C-p>", pickers.find_files, { desc = "Find files" })
map("n", "<C-S-p>", pickers.commands, { desc = "Command palette" })
map("n", "<C-S-f>", pickers.live_grep, { desc = "Search in workspace" })
map("n", "<C-S-o>", pickers.document_symbols, { desc = "Document symbols" })
map("n", "<C-t>", pickers.workspace_symbols, { desc = "Workspace symbols" })

map("n", "<C-/>", "gcc", { remap = true, desc = "Toggle comment" })
map("v", "<C-/>", "gc", { remap = true, desc = "Toggle comment (visual)" })

map("n", "<C-n>", file_creation.create, { desc = "Create file in current directory" })
map("n", "<C-b>", file_explorer.toggle_visibility, { desc = "Toggle file explorer" })
map("n", "<C-S-e>", file_explorer.toggle_focus, { desc = "Toggle file explorer focus" })
map("n", "<C-`>", terminal.toggle, { desc = "Toggle terminal" })

map({ "n", "i" }, "<C-S-j>", "<cmd>vertical resize +2<cr>", { desc = "Increase window width" })
map({ "n", "i" }, "<C-S-k>", "<cmd>vertical resize -2<cr>", { desc = "Decrease window width" })

map("n", "<F2>", vim.lsp.buf.rename, { desc = "Rename symbol" })
map("n", "<F12>", vim.lsp.buf.definition, { desc = "Go to definition" })
map("n", "<S-F12>", pickers.references, { desc = "Find references" })
map("n", "<C-.>", vim.lsp.buf.code_action, { desc = "Code action" })
map({ "n", "i" }, "<C-S-Space>", vim.lsp.buf.signature_help, { desc = "Signature help" })

map("n", "<A-Up>", "<cmd>m .-2<cr>==", { desc = "Move line up" })
map("n", "<A-Down>", "<cmd>m .+1<cr>==", { desc = "Move line down" })
map("v", "<A-Up>", ":m '<-2<cr>gv=gv", { desc = "Move selection up" })
map("v", "<A-Down>", ":m '>+1<cr>gv=gv", { desc = "Move selection down" })

map("n", "<leader>w", "<cmd>w<cr>", { desc = "Save file" })
map("n", "<leader>c", "<cmd>bd<cr>", { desc = "Close buffer" })
map("n", "<C-w>", buffer_closing.close, { desc = "Close buffer (focus next or prev)", nowait = true })
map("i", "<C-w>", buffer_closing.close_from_insert, { desc = "Close buffer (focus next or prev)", nowait = true })

map({ "n", "i" }, "<C-PageUp>", "<cmd>BufferLineCyclePrev<cr>", { desc = "Previous open file" })
map({ "n", "i" }, "<C-PageDown>", "<cmd>BufferLineCycleNext<cr>", { desc = "Next open file" })

map({ "n", "v" }, "<leader>y", [["+y]], { desc = "Yank to system clipboard" })
map("n", "<leader>Y", [["+Y]], { desc = "Yank line to system clipboard" })
map({ "n", "v" }, "<leader>D", [["_d]], { desc = "Delete without yanking" })

map("n", "<C-u>", "<C-u>zz", { desc = "Half-page up (centered)" })
map("n", "<C-d>", "<C-d>zz", { desc = "Half-page down (centered)" })
map("n", "n", "nzzzv", { desc = "Next search match (centered)" })
map("n", "N", "Nzzzv", { desc = "Prev search match (centered)" })

map("n", "<C-Up>", "<C-y>", { desc = "Scroll view up one line" })
map("n", "<C-Down>", "<C-e>", { desc = "Scroll view down one line" })
map("i", "<C-Up>", "<C-o><C-y>", { desc = "Scroll view up one line" })
map("i", "<C-Down>", "<C-o><C-e>", { desc = "Scroll view down one line" })
map("v", "<C-Up>", "<C-y>", { desc = "Scroll view up one line" })
map("v", "<C-Down>", "<C-e>", { desc = "Scroll view down one line" })

map({ "n", "i", "v" }, "<C-S-Down>", ten_line_jumping.jump_buffer_down, { desc = "Jump 10 lines down" })
map({ "n", "i", "v" }, "<C-S-Up>", ten_line_jumping.jump_buffer_up, { desc = "Jump 10 lines up" })

map("v", "K", ":m '<-2<cr>gv=gv", { silent = true, desc = "Move block up" })
map("v", "J", ":m '>+1<cr>gv=gv", { silent = true, desc = "Move block down" })

map("x", "p", [["_dP]], { desc = "Paste without yanking replaced text" })
map("i", "<C-c>", "<esc>", { desc = "Escape" })

command_line_abbreviations.install()
lazyvim_defaults.rebind_window_navigation_to_bypass_the_buffer_close_chord()
