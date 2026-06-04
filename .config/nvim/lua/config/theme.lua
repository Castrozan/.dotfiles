local wallpaper_palette = require("config.theme.wallpaper_palette")
local transparency = require("config.theme.transparency")
local markdown_heading_backgrounds = require("config.theme.markdown_heading_backgrounds")

local dynamic_theme = {}

local theme_change_signal_file_path = vim.fn.expand("~/.config/hypr-theme/current/theme.name")

local active_background_hex = "#05070e"

local function schedule_background_clear()
  vim.schedule(function()
    transparency.clear_backgrounds_to_let_terminal_show_through()
    markdown_heading_backgrounds.soften_against_background(active_background_hex)
  end)
end

function dynamic_theme.apply()
  local base16_module_is_available, base16_module = pcall(require, "base16-colorscheme")
  if not base16_module_is_available then
    return
  end
  local base16_palette = wallpaper_palette.read_and_map_to_base16()
  active_background_hex = base16_palette.base00
  base16_module.setup(base16_palette)
  schedule_background_clear()
end

local wallpaper_theme_change_watcher

local function arm_wallpaper_theme_change_watcher()
  if not wallpaper_theme_change_watcher then
    return
  end
  pcall(function()
    wallpaper_theme_change_watcher:start(
      theme_change_signal_file_path,
      {},
      vim.schedule_wrap(function()
        dynamic_theme.apply()
        wallpaper_theme_change_watcher:stop()
        arm_wallpaper_theme_change_watcher()
      end)
    )
  end)
end

function dynamic_theme.setup_live_reload_on_wallpaper_change()
  if not wallpaper_theme_change_watcher then
    wallpaper_theme_change_watcher = vim.uv.new_fs_event()
    arm_wallpaper_theme_change_watcher()
  end

  vim.api.nvim_create_autocmd("FocusGained", {
    group = vim.api.nvim_create_augroup("ReapplyDynamicThemeOnFocusGained", { clear = true }),
    callback = function()
      dynamic_theme.apply()
    end,
  })

  vim.api.nvim_create_autocmd("ColorScheme", {
    group = vim.api.nvim_create_augroup("ReclearBackgroundsAfterColorscheme", { clear = true }),
    callback = schedule_background_clear,
  })

  vim.api.nvim_create_autocmd("FileType", {
    group = vim.api.nvim_create_augroup("ReclearBackgroundsWhenSnacksPickerOpens", { clear = true }),
    pattern = { "snacks_picker_list", "snacks_layout_box", "snacks_picker_input" },
    callback = schedule_background_clear,
  })

  vim.api.nvim_create_user_command("ThemeReload", function()
    dynamic_theme.apply()
  end, { desc = "Re-read the wallpaper palette and re-apply the dynamic theme" })
end

return dynamic_theme
