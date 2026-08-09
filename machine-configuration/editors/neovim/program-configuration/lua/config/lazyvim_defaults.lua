local lazyvim_defaults = {}

local window_resize_defaults_this_config_deletes = {
  { mode = "n", chord = "<C-Left>" },
  { mode = "n", chord = "<C-Right>" },
  { mode = "n", chord = "<C-Up>" },
  { mode = "n", chord = "<C-Down>" },
}

local window_navigation_defaults_that_expand_the_buffer_close_chord = {
  { chord = "<C-h>", direction = "h", description = "Go to Left Window" },
  { chord = "<C-j>", direction = "j", description = "Go to Lower Window" },
  { chord = "<C-k>", direction = "k", description = "Go to Upper Window" },
  { chord = "<C-l>", direction = "l", description = "Go to Right Window" },
}

function lazyvim_defaults.remove_window_resize_keymaps()
  for _, deleted in ipairs(window_resize_defaults_this_config_deletes) do
    pcall(vim.keymap.del, deleted.mode, deleted.chord)
  end
end

function lazyvim_defaults.rebind_window_navigation_to_bypass_the_buffer_close_chord()
  for _, navigation in ipairs(window_navigation_defaults_that_expand_the_buffer_close_chord) do
    local go_to_window = "<cmd>wincmd " .. navigation.direction .. "<cr>"
    vim.keymap.set("n", navigation.chord, go_to_window, { desc = navigation.description })
  end
end

return lazyvim_defaults
