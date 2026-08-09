local function clear_hidden_flag_so_only_gitignored_entries_render_dimmed(item)
  item.hidden = false
end

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
            exclude = { ".git" },
            transform = clear_hidden_flag_so_only_gitignored_entries_render_dimmed,
            win = {
              list = {
                keys = {
                  ["<c-p>"] = false,
                  ["<c-n>"] = "explorer_add",
                },
              },
            },
          },
        },
      },
    },
  },
}
