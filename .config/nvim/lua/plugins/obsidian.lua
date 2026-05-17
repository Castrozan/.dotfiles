return {
  {
    "epwalsh/obsidian.nvim",
    version = "*",
    lazy = true,
    ft = "markdown",
    dependencies = { "nvim-lua/plenary.nvim" },
    keys = {
      { "<leader>oo", "<cmd>ObsidianOpen<cr>", desc = "Obsidian open in app" },
      { "<leader>on", "<cmd>ObsidianNew<cr>", desc = "Obsidian new note" },
      { "<leader>os", "<cmd>ObsidianSearch<cr>", desc = "Obsidian search" },
      { "<leader>oq", "<cmd>ObsidianQuickSwitch<cr>", desc = "Obsidian quick switch" },
      { "<leader>ot", "<cmd>ObsidianTemplate<cr>", desc = "Obsidian insert template" },
      { "<leader>od", "<cmd>ObsidianToday<cr>", desc = "Obsidian today's daily note" },
      { "<leader>ob", "<cmd>ObsidianBacklinks<cr>", desc = "Obsidian backlinks" },
    },
    opts = {
      workspaces = {
        {
          name = "Zanoni",
          path = vim.env.OBSIDIAN_HOME or (vim.env.HOME .. "/vault"),
        },
      },
      notes_subdir = "inbox",
      new_notes_location = "notes_subdir",
      disable_frontmatter = true,
      templates = {
        subdir = "templates",
        date_format = "%Y-%m-%d",
        time_format = "%H:%M:%S",
      },
      completion = {
        nvim_cmp = true,
        min_chars = 2,
      },
      ui = {
        checkboxes = {},
        bullets = {},
      },
      mappings = {
        ["gf"] = {
          action = function()
            return require("obsidian").util.gf_passthrough()
          end,
          opts = { noremap = false, expr = true, buffer = true },
        },
      },
    },
  },
}
