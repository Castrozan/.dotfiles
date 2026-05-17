return {
  {
    "mason-org/mason.nvim",
    enabled = false,
  },
  {
    "mason-org/mason-lspconfig.nvim",
    enabled = false,
  },
  {
    "jay-babu/mason-nvim-dap.nvim",
    enabled = false,
  },
  {
    "neovim/nvim-lspconfig",
    opts = {
      servers = {
        nixd = {
          settings = {
            nixd = {
              formatting = { command = { "nixfmt" } },
            },
          },
        },
        lua_ls = {},
        pyright = {},
        ruff = {},
        ts_ls = {},
        rust_analyzer = {},
        gopls = {},
        bashls = {},
        marksman = {},
        terraformls = {},
      },
      setup = {
        rust_analyzer = function()
          return true
        end,
      },
    },
  },
  {
    "stevearc/conform.nvim",
    opts = {
      formatters_by_ft = {
        nix = { "nixfmt" },
        python = { "ruff_format" },
        lua = { "stylua" },
        javascript = { "prettier" },
        typescript = { "prettier" },
        javascriptreact = { "prettier" },
        typescriptreact = { "prettier" },
        json = { "prettier" },
        yaml = { "prettier" },
        markdown = { "prettier" },
        rust = { "rustfmt" },
        go = { "gofmt" },
        sh = { "shfmt" },
      },
    },
  },
  {
    "mfussenegger/nvim-lint",
    opts = {
      linters_by_ft = {
        nix = { "statix" },
        python = { "ruff" },
        sh = { "shellcheck" },
        markdown = { "markdownlint-cli2" },
      },
    },
  },
}
