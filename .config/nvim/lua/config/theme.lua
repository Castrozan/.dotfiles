local dynamic_theme = {}

local theme_change_signal_file_path = vim.fn.expand("~/.config/hypr-theme/current/theme.name")

local function schedule_background_clear()
  vim.schedule(require("config.theme.transparency").clear_backgrounds_to_let_terminal_show_through)
end

function dynamic_theme.apply()
  local base16_module_is_available, base16_module = pcall(require, "base16-colorscheme")
  if not base16_module_is_available then
    return
  end
  local base16_palette = require("config.theme.wallpaper_palette").read_and_map_to_base16()
  base16_module.setup(base16_palette)
  schedule_background_clear()
  vim.schedule(function()
    require("config.theme.markdown_highlights").apply(base16_palette)
  end)
end

local function forget_cached_theme_submodules_so_next_require_reads_disk()
  for module_name in pairs(package.loaded) do
    if module_name:match("^config%.theme%.") then
      package.loaded[module_name] = nil
    end
  end
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
    forget_cached_theme_submodules_so_next_require_reads_disk()
    dynamic_theme.apply()
  end, { desc = "Reload theme submodules from disk and re-apply the dynamic theme" })
end

return dynamic_theme
