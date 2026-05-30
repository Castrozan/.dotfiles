return {
  {
    "RRethy/base16-nvim",
    lazy = false,
    priority = 1000,
  },
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = function()
        require("config.theme").apply()
        require("config.theme").setup_live_reload_on_wallpaper_change()
      end,
    },
  },
}
