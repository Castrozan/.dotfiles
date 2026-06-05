local return_to_last_edit_position_group = vim.api.nvim_create_augroup("ReturnToLastEditPosition", { clear = true })
vim.api.nvim_create_autocmd("BufReadPost", {
  group = return_to_last_edit_position_group,
  pattern = "*",
  callback = function()
    local last_position = vim.fn.line("'\"")
    if last_position > 0 and last_position <= vim.fn.line("$") then
      vim.cmd('normal! g`"')
    end
  end,
})

local quiet_listchars_in_prose_group = vim.api.nvim_create_augroup("QuietListcharsInProse", { clear = true })
vim.api.nvim_create_autocmd("FileType", {
  group = quiet_listchars_in_prose_group,
  pattern = { "markdown", "norg", "rmd", "org" },
  callback = function()
    vim.wo.list = false
  end,
})

local trim_trailing_whitespace_on_save_group =
  vim.api.nvim_create_augroup("TrimTrailingWhitespaceOnSave", { clear = true })
vim.api.nvim_create_autocmd("BufWritePre", {
  group = trim_trailing_whitespace_on_save_group,
  pattern = "*",
  callback = function()
    local save_view = vim.fn.winsaveview()
    vim.cmd([[silent! %s/\s\+$//e]])
    vim.fn.winrestview(save_view)
  end,
})
