# LSP binaries and custom marketplace for Claude Code
{ pkgs, ... }:
let
  # Custom marketplace for LSP plugins not in official marketplace
  customMarketplace = {
    "$schema" = "https://anthropic.com/claude-code/marketplace.schema.json";
    name = "custom-lsp";
    description = "Custom LSP plugins for Nix and Bash language support";
    owner = {
      name = "zanoni";
      email = "lucas@zanoni.dev";
    };
    plugins = [
      {
        name = "nixd-lsp";
        description = "Nix language server for code intelligence and diagnostics";
        version = "1.0.0";
        author = {
          name = "zanoni";
          email = "lucas@zanoni.dev";
        };
        source = "./plugins/nixd-lsp";
        category = "development";
        strict = false;
        lspServers = {
          nixd = {
            command = "nixd";
            extensionToLanguage = {
              ".nix" = "nix";
            };
          };
        };
      }
      {
        name = "bash-lsp";
        description = "Bash language server for shell script intelligence";
        version = "1.0.0";
        author = {
          name = "zanoni";
          email = "lucas@zanoni.dev";
        };
        source = "./plugins/bash-lsp";
        category = "development";
        strict = false;
        lspServers = {
          bash = {
            command = "bash-language-server";
            args = [ "start" ];
            extensionToLanguage = {
              ".sh" = "shellscript";
              ".bash" = "shellscript";
              ".zsh" = "shellscript";
            };
          };
        };
      }
    ];
  };

  # Known marketplaces registration
  knownMarketplaces = [
    {
      name = "claude-plugins-official";
      path = "~/.claude/plugins/marketplaces/claude-plugins-official";
    }
    {
      name = "custom-lsp";
      path = "~/.claude/plugins/marketplaces/custom-lsp";
    }
  ];
in
{
  home.packages = with pkgs; [
    # TypeScript/JavaScript
    typescript-language-server
    typescript

    # Java
    jdt-language-server

    # Nix
    nixd
    nixfmt-rfc-style

    # Bash/shell
    bash-language-server
  ];

  # Custom marketplace structure
  home.file = {
    # Marketplace definition
    ".claude/plugins/marketplaces/custom-lsp/.claude-plugin/marketplace.json".text =
      builtins.toJSON customMarketplace;

    # Plugin READMEs (required for valid plugin structure)
    ".claude/plugins/marketplaces/custom-lsp/plugins/nixd-lsp/README.md".text = ''
      # nixd-lsp

      Nix language server plugin for Claude Code.

      Provides code intelligence, diagnostics, and completion for `.nix` files using [nixd](https://github.com/nix-community/nixd).

      ## Requirements

      - `nixd` must be installed and available in PATH
    '';

    ".claude/plugins/marketplaces/custom-lsp/plugins/bash-lsp/README.md".text = ''
      # bash-lsp

      Bash language server plugin for Claude Code.

      Provides code intelligence for shell scripts (`.sh`, `.bash`, `.zsh`) using [bash-language-server](https://github.com/bash-lsp/bash-language-server).

      ## Requirements

      - `bash-language-server` must be installed and available in PATH
    '';

    # Register custom marketplace
    ".claude/known_marketplaces.json".text = builtins.toJSON knownMarketplaces;
  };
}
