local function toggle_directory_under_cursor()
  local explorer_picker = Snacks.picker.get({ source = "explorer" })[1]
  if not explorer_picker then
    return
  end
  local item_under_cursor = explorer_picker:current()
  if item_under_cursor and item_under_cursor.dir then
    explorer_picker:action("confirm")
  end
end

local function yank_selected_paths_without_trailing_newline()
  local explorer_picker = Snacks.picker.get({ source = "explorer" })[1]
  if not explorer_picker then
    return
  end
  if vim.fn.mode():find("^[vV]") then
    explorer_picker.list:select()
  end
  local selected_paths = {}
  for _, item in ipairs(explorer_picker:selected({ fallback = true })) do
    table.insert(selected_paths, Snacks.picker.util.path(item))
  end
  explorer_picker.list:set_selected()
  vim.fn.setreg(vim.v.register or "+", table.concat(selected_paths, "\n"), "c")
  Snacks.notify.info("Yanked " .. #selected_paths .. " files")
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
            win = {
              list = {
                keys = {
                  ["<c-n>"] = "explorer_add",
                  ["<c-k>"] = false,
                  ["<c-k>e"] = toggle_directory_under_cursor,
                  ["y"] = { yank_selected_paths_without_trailing_newline, mode = { "n", "x" } },
                },
              },
            },
          },
        },
      },
    },
  },
}
