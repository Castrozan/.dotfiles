vim.g.snacks_animate = false

local options = vim.opt

options.spell = true
options.spelllang = { "en" }
options.scrolloff = 8
options.sidescrolloff = 8
options.tabstop = 4
options.softtabstop = 4
options.shiftwidth = 4
options.expandtab = true
options.undodir = vim.fn.expand("~/.vim/undodir")
options.undofile = true
options.swapfile = false
options.backup = false
options.signcolumn = "yes"
options.updatetime = 50
options.listchars = {
  tab = "» ",
  extends = "›",
  precedes = "‹",
  nbsp = "·",
  trail = "·",
}
options.list = true

local two_space_indent_group = vim.api.nvim_create_augroup("TwoSpaceIndentForWebFiletypes", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = two_space_indent_group,
  pattern = {
    "javascript",
    "javascriptreact",
    "typescript",
    "typescriptreact",
    "html",
    "css",
    "scss",
    "lua",
    "json",
    "yaml",
    "nix",
  },
  callback = function()
    vim.bo.tabstop = 2
    vim.bo.softtabstop = 2
    vim.bo.shiftwidth = 2
  end,
})

local python_column_guide_group = vim.api.nvim_create_augroup("PythonColumnGuide", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = python_column_guide_group,
  pattern = "python",
  callback = function()
    vim.bo.textwidth = 79
    vim.wo.colorcolumn = "79"
  end,
})
