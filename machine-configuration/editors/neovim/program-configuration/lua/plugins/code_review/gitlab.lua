return {
  {
    "harrisoncramer/gitlab.nvim",
    lazy = true,
    dependencies = {
      "MunifTanjim/nui.nvim",
      "nvim-lua/plenary.nvim",
      "sindrets/diffview.nvim",
    },
    build = function()
      require("gitlab.server").build(true)
    end,
    opts = {
      auth_provider = function()
        return require("config.code_review.gitlab_authentication").provide()
      end,
      discussion_tree = {
        draft_mode = true,
      },
    },
  },
}
