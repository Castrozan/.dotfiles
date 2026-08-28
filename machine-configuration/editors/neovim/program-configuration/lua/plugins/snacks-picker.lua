local line_jumping = require("config.navigation.line_jumping")

return {
  {
    "folke/snacks.nvim",
    opts = {
      picker = {
        layout = {
          cycle = false,
        },
        actions = {
          jump_selection_down = line_jumping.jump_snacks_selection_down,
          jump_selection_up = line_jumping.jump_snacks_selection_up,
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
