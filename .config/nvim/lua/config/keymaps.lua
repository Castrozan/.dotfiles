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

map("n", "<C-b>", "<cmd>Neotree toggle<cr>", { desc = "Toggle file explorer" })
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

map("n", "<A-Up>", "<cmd>m .-2<cr>==", { desc = "Move line up" })
map("n", "<A-Down>", "<cmd>m .+1<cr>==", { desc = "Move line down" })
map("v", "<A-Up>", ":m '<-2<cr>gv=gv", { desc = "Move selection up" })
map("v", "<A-Down>", ":m '>+1<cr>gv=gv", { desc = "Move selection down" })

map("n", "<leader>w", "<cmd>w<cr>", { desc = "Save file" })
map("n", "<leader>c", "<cmd>bd<cr>", { desc = "Close buffer" })

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
