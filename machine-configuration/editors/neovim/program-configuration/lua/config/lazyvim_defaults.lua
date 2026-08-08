local lazyvim_defaults = {}

local keymaps_this_config_replaces = {
  { mode = "n", chord = "<C-Left>" },
  { mode = "n", chord = "<C-Right>" },
}

function lazyvim_defaults.remove_replaced_keymaps()
  for _, replaced in ipairs(keymaps_this_config_replaces) do
    pcall(vim.keymap.del, replaced.mode, replaced.chord)
  end
end

return lazyvim_defaults
