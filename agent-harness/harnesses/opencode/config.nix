{
  pkgs,
  config,
  lib,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  opencodeGo = import ./go-provider.nix { homeDirectory = homeDir; };

  defaultOpencodeModel = "opencode/big-pickle";
  titleGenerationModel = "opencode-go/${opencodeGo.models.haiku}";

  opencodePluginSettings = pkgs.runCommand "opencode-plugin-settings.json" { } ''
    ${pkgs.jq}/bin/jq -r '
      .mcp."plugin.dotfiles.chrome-devtools".timeout = 120000 |
      .mcp."plugin.dotfiles.sonarqube".timeout = 60000 |
      tojson |
      gsub("\\{env:"; "\\u007benv:") |
      gsub("\\{file:"; "\\u007bfile:")
    ' ${config.agentPlugins.bundle}/.opencode/opencode.jsonc > "$out"
  '';

  opencodePythonLspEnvironment =
    import ../../../machine-configuration/development/testing/python-test-environment.nix
      {
        inherit pkgs;
      };

  fullAccessPermissions = [
    {
      action = "*";
      resource = "*";
      effect = "allow";
    }
  ];

  opencodeGlobalSettings = {
    "$schema" = "https://opencode.ai/v2/config.json";
    update = "disable";
    share = "manual";
    snapshots = true;

    model = defaultOpencodeModel;
    default_agent = "build";

    instructions = [ "~/.config/opencode/AGENTS.md" ];

    permissions = fullAccessPermissions;

    lsp = {
      pyright = {
        command = [
          "${pkgs.pyright}/bin/pyright-langserver"
          "--stdio"
        ];
        env = {
          PYTHONPATH = "${opencodePythonLspEnvironment}/lib/python3.12/site-packages";
        };
      };
    };
    formatter = true;

    compaction = {
      auto = true;
    };

    watcher = {
      ignore = [
        ".git/**"
        "node_modules/**"
        "dist/**"
        "result/**"
        "result-*/**"
        ".direnv/**"
      ];
    };

    experimental = {
      subagent_depth = 2;
    };

    agents = {
      build = {
        mode = "primary";
        description = "Full-access coding agent with all tools enabled";
        model = "${defaultOpencodeModel}#max";
        permissions = fullAccessPermissions;
      };
      plan = {
        mode = "primary";
        description = "Read-only architect that designs a change without editing files";
        model = "${defaultOpencodeModel}#max";
      };
      title.model = titleGenerationModel;
    };
  };
in
{
  imports = [ ../../agent-instructions/production-plugin/home-manager.nix ];

  home = {
    activation = {
      prepareOpenCodePluginData = lib.hm.dag.entryBetween [ "linkGeneration" ] [ "writeBoundary" ] ''
        run ${pkgs.coreutils}/bin/mkdir -p ${lib.escapeShellArg "${config.agentPlugins.opencodeDataRoot}/dotfiles"}
      '';

      retireOpenCodePluginProjections = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
        ${pkgs.python312}/bin/python3 ${../../agent-instructions/production-plugin/scripts/retire-projections.py} \
          opencode "${config.home.homeDirectory}" ${config.agentPlugins.bundle}
      '';
    };

    file = {
      ".config/opencode/.keep".text = "";
      ".config/opencode/opencode.json".text = builtins.toJSON opencodeGlobalSettings;
      ".config/opencode/opencode.jsonc".source = opencodePluginSettings;
    };

    sessionVariables = {
      OPENCODE_AUTO_UPDATE = "false";
      OPENCODE_DISABLE_CLAUDE_CODE_SKILLS = "true";
    };
  };
}
