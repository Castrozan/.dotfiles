return {
  {
    "folke/zen-mode.nvim",
    cmd = "ZenMode",
    keys = {
      { "<leader>z", "<cmd>ZenMode<cr>", desc = "Zen mode toggle" },
    },
    opts = {
      window = {
        width = 0.85,
      },
      plugins = {
        twilight = { enabled = true },
        gitsigns = { enabled = false },
      },
    },
  },
  {
    "folke/twilight.nvim",
    cmd = "Twilight",
    opts = {},
  },
}
