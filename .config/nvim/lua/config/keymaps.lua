local map = vim.keymap.set

map({ "n", "i", "v" }, "<C-s>", "<cmd>w<cr><esc>", { desc = "Save file" })
map("n", "<C-q>", "<cmd>qa<cr>", { desc = "Quit all" })

map("n", "<C-p>", function()
  require("telescope.builtin").find_files()
end, { desc = "Find files" })
map("n", "<C-S-p>", function()
  require("telescope.builtin").commands()
end, { desc = "Command palette" })
map("n", "<C-S-f>", function()
  require("telescope.builtin").live_grep()
end, { desc = "Search in workspace" })
map("n", "<C-S-o>", function()
  require("telescope.builtin").lsp_document_symbols()
end, { desc = "Document symbols" })
map("n", "<C-t>", function()
  require("telescope.builtin").lsp_dynamic_workspace_symbols()
end, { desc = "Workspace symbols" })

map("n", "<C-/>", "gcc", { remap = true, desc = "Toggle comment" })
map("v", "<C-/>", "gc", { remap = true, desc = "Toggle comment (visual)" })

map("n", "<leader>r", function()
  for module_name, _ in pairs(package.loaded) do
    if module_name:match("^config%.") then
      package.loaded[module_name] = nil
    end
  end
  vim.cmd("source " .. vim.fn.stdpath("config") .. "/lua/config/keymaps.lua")
  vim.cmd("source " .. vim.fn.stdpath("config") .. "/lua/config/options.lua")
  vim.cmd("source " .. vim.fn.stdpath("config") .. "/lua/config/autocmds.lua")
  vim.notify("nvim config reloaded", vim.log.levels.INFO)
end, { desc = "Reload nvim config (keymaps/options/autocmds)" })

map("n", "<C-b>", function()
  Snacks.explorer()
end, { desc = "Toggle file explorer" })
require("config.file_explorer")
map("n", "<C-`>", function()
  Snacks.terminal()
end, { desc = "Toggle terminal" })

map("n", "<F2>", vim.lsp.buf.rename, { desc = "Rename symbol" })
map("n", "<F12>", vim.lsp.buf.definition, { desc = "Go to definition" })
map("n", "<S-F12>", function()
  require("telescope.builtin").lsp_references()
end, { desc = "Find references" })
map("n", "<C-.>", vim.lsp.buf.code_action, { desc = "Code action" })
map({ "n", "i" }, "<C-S-Space>", vim.lsp.buf.signature_help, { desc = "Signature help" })

map("n", "<C-Up>", "<C-y>", { desc = "Scroll view up one line" })
map("n", "<C-Down>", "<C-e>", { desc = "Scroll view down one line" })
map("i", "<C-Up>", "<C-o><C-y>", { desc = "Scroll view up one line" })
map("i", "<C-Down>", "<C-o><C-e>", { desc = "Scroll view down one line" })
map("v", "<C-Up>", "<C-y>", { desc = "Scroll view up one line" })
map("v", "<C-Down>", "<C-e>", { desc = "Scroll view down one line" })

map("n", "<C-Right>", "w", { desc = "Jump to next word" })
map("n", "<C-Left>", "b", { desc = "Jump to previous word" })
map("i", "<C-Right>", "<C-o>w", { desc = "Jump to next word" })
map("i", "<C-Left>", "<C-o>b", { desc = "Jump to previous word" })
map("v", "<C-Right>", "w", { desc = "Jump to next word" })
map("v", "<C-Left>", "b", { desc = "Jump to previous word" })

map("n", "<C-S-Down>", "10jzz", { desc = "Jump 10 lines down" })
map("n", "<C-S-Up>", "10kzz", { desc = "Jump 10 lines up" })
map("i", "<C-S-Down>", "<esc>10jzzi", { desc = "Jump 10 lines down" })
map("i", "<C-S-Up>", "<esc>10kzzi", { desc = "Jump 10 lines up" })
map("v", "<C-S-Down>", "10jzz", { desc = "Jump 10 lines down" })
map("v", "<C-S-Up>", "10kzz", { desc = "Jump 10 lines up" })

map("n", "<C-PageUp>", "<cmd>BufferLineCyclePrev<cr>", { desc = "Previous open file" })
map("n", "<C-PageDown>", "<cmd>BufferLineCycleNext<cr>", { desc = "Next open file" })
map("i", "<C-PageUp>", "<cmd>BufferLineCyclePrev<cr>", { desc = "Previous open file" })
map("i", "<C-PageDown>", "<cmd>BufferLineCycleNext<cr>", { desc = "Next open file" })

map("n", "<A-Up>", "<cmd>m .-2<cr>==", { desc = "Move line up" })
map("n", "<A-Down>", "<cmd>m .+1<cr>==", { desc = "Move line down" })
map("v", "<A-Up>", ":m '<-2<cr>gv=gv", { desc = "Move selection up" })
map("v", "<A-Down>", ":m '>+1<cr>gv=gv", { desc = "Move selection down" })

map("n", "<leader>w", "<cmd>w<cr>", { desc = "Save file" })

local function find_other_listed_file_buffer_than(excluded_buffer_id)
  for _, buffer_id in ipairs(vim.api.nvim_list_bufs()) do
    if
      buffer_id ~= excluded_buffer_id
      and vim.api.nvim_buf_is_valid(buffer_id)
      and vim.bo[buffer_id].buflisted
      and vim.api.nvim_buf_get_name(buffer_id) ~= ""
    then
      return buffer_id
    end
  end
  return nil
end

local function current_buffer_represents_a_file()
  return vim.bo.buflisted and vim.api.nvim_buf_get_name(0) ~= ""
end

local function close_current_buffer_focusing_right_then_left()
  local buffer_to_close = vim.api.nvim_get_current_buf()
  if current_buffer_represents_a_file() and not find_other_listed_file_buffer_than(buffer_to_close) then
    Snacks.dashboard({ win = vim.api.nvim_get_current_win() })
    vim.cmd("bdelete " .. buffer_to_close)
    return
  end
  vim.cmd("BufferLineCycleNext")
  if vim.api.nvim_get_current_buf() == buffer_to_close then
    vim.cmd("BufferLineCyclePrev")
  end
  vim.cmd("bdelete " .. buffer_to_close)
end

map("n", "<leader>c", close_current_buffer_focusing_right_then_left, { desc = "Close buffer" })
map("n", "<C-w>", close_current_buffer_focusing_right_then_left, { desc = "Close buffer (focus next or prev)" })
map("i", "<C-w>", function()
  vim.cmd("stopinsert")
  close_current_buffer_focusing_right_then_left()
end, { desc = "Close buffer (focus next or prev)" })

map({ "n", "v" }, "<leader>y", [["+y]], { desc = "Yank to system clipboard" })
map("n", "<leader>Y", [["+Y]], { desc = "Yank line to system clipboard" })
map({ "n", "v" }, "<leader>D", [["_d]], { desc = "Delete without yanking" })

map("n", "<C-u>", "<C-u>zz", { desc = "Half-page up (centered)" })
map("n", "<C-d>", "<C-d>zz", { desc = "Half-page down (centered)" })
map("n", "n", "nzzzv", { desc = "Next search match (centered)" })
map("n", "N", "Nzzzv", { desc = "Prev search match (centered)" })

map("v", "K", ":m '<-2<cr>gv=gv", { silent = true, desc = "Move block up" })
map("v", "J", ":m '>+1<cr>gv=gv", { silent = true, desc = "Move block down" })

map("x", "p", [["_dP]], { desc = "Paste without yanking replaced text" })
map("i", "<C-c>", "<esc>", { desc = "Escape" })

vim.cmd("cnoreabbrev W w")
vim.cmd("cnoreabbrev Q q")
vim.cmd("cnoreabbrev Wq wq")
vim.cmd("cnoreabbrev WQ wq")
