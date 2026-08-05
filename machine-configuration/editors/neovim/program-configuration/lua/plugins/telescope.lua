local paste_system_clipboard_as_single_line = function()
  require("config.clipboard").paste_system_clipboard_as_single_line()
end

return {
  {
    "nvim-telescope/telescope.nvim",
    opts = {
      defaults = {
        mappings = {
          i = { ["<C-v>"] = paste_system_clipboard_as_single_line },
          n = { ["<C-v>"] = paste_system_clipboard_as_single_line },
        },
      },
    },
  },
}
