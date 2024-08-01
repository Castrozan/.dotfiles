
-- New maker to ignore files bigger than a threshold
-- inspired by: https://github.com/nvim-telescope/telescope.nvim/issues/623
local previewers = require('telescope.previewers')
local Job = require('plenary.job')

local new_maker = function(filepath, bufnr, opts)
  filepath = vim.fn.expand(filepath)
  Job:new({
    command = 'wc',
    args = {'-c', filepath},
    on_exit = function(j)
      local result = j:result()[1]
      local file_size = tonumber(result:match('%d+'))
      if file_size > 100000 then  -- Set your size threshold here (e.g., 100000 bytes = 100 KB)
        return
      else
        previewers.buffer_previewer_maker(filepath, bufnr, opts)
      end
    end
  }):sync()
end

-- See `:help telescope` and `:help telescope.setup()`
require('telescope').setup {
  defaults = {
    buffer_previewer_maker = new_maker,
    layout_strategy = "vertical",
    vimgrep_arguments = {
    },
    file_ignore_patterns = {
      "node_modules", --"build", "dist", "yarn.lock"
    },
    layout_config = {
      preview_height = 0.7,
      vertical = {
        size = {
          width = "95%",
          height = "95%",
        },
      },
    },
  },
}

-- vim.keymap.set("n", "<Leader>sn", "<CMD>lua require('telescope').extensions.notify.notify()<CR>", silent)

