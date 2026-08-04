local paste_system_clipboard_as_single_line = function()
  require("config.clipboard").paste_system_clipboard_as_single_line()
end

local ignore_key_press_on_the_result_list = function() end

return {
  {
    "folke/snacks.nvim",
    opts = {
      picker = {
        win = {
          input = {
            keys = {
              ["<c-v>"] = { paste_system_clipboard_as_single_line, mode = { "i", "n" } },
            },
          },
          list = {
            keys = {
              ["<c-v>"] = { ignore_key_press_on_the_result_list, mode = { "n", "x" } },
            },
          },
        },
      },
    },
  },
}
