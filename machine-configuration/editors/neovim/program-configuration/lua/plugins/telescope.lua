local line_jumping = require("config.navigation.line_jumping")

return {
  {
    "nvim-telescope/telescope.nvim",
    opts = {
      defaults = {
        scroll_strategy = "limit",
        mappings = {
          i = {
            ["<C-S-Down>"] = line_jumping.jump_telescope_selection_down,
            ["<C-S-Up>"] = line_jumping.jump_telescope_selection_up,
          },
          n = {
            ["<C-S-Down>"] = line_jumping.jump_telescope_selection_down,
            ["<C-S-Up>"] = line_jumping.jump_telescope_selection_up,
          },
        },
      },
    },
  },
}
