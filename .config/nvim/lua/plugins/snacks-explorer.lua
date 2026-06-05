return {
  {
    "folke/snacks.nvim",
    opts = {
      picker = {
        sources = {
          explorer = {
            hidden = true,
            follow = true,
            ignored = true,
            win = {
              list = {
                keys = {
                  ["<c-n>"] = "explorer_add",
                  ["<c-k>"] = false,
                  ["<c-k>e"] = "confirm",
                },
              },
            },
          },
        },
      },
    },
  },
}
