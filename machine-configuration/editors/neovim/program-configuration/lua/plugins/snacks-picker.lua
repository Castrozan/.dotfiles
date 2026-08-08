local ten_line_jumping = require("config.navigation.ten_line_jumping")

return {
  {
    "folke/snacks.nvim",
    opts = {
      picker = {
        layout = {
          cycle = false,
        },
        actions = {
          jump_selection_down = ten_line_jumping.jump_snacks_selection_down,
          jump_selection_up = ten_line_jumping.jump_snacks_selection_up,
        },
        win = {
          input = {
            keys = {
              ["<C-S-Down>"] = { "jump_selection_down", mode = { "i", "n" } },
              ["<C-S-Up>"] = { "jump_selection_up", mode = { "i", "n" } },
            },
          },
          list = {
            keys = {
              ["<C-S-Down>"] = "jump_selection_down",
              ["<C-S-Up>"] = "jump_selection_up",
            },
          },
        },
      },
    },
  },
}
