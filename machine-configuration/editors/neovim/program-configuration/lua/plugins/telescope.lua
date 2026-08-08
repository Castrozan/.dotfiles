local ten_line_jumping = require("config.navigation.ten_line_jumping")

return {
  {
    "nvim-telescope/telescope.nvim",
    opts = {
      defaults = {
        scroll_strategy = "limit",
        mappings = {
          i = {
            ["<C-S-Down>"] = ten_line_jumping.jump_telescope_selection_down,
            ["<C-S-Up>"] = ten_line_jumping.jump_telescope_selection_up,
          },
          n = {
            ["<C-S-Down>"] = ten_line_jumping.jump_telescope_selection_down,
            ["<C-S-Up>"] = ten_line_jumping.jump_telescope_selection_up,
          },
        },
      },
    },
  },
}
