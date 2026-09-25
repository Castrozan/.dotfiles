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

  fullAccessPermissions = {
    "*" = "allow";
    read = "allow";
    edit = "allow";
    glob = "allow";
    grep = "allow";
    list = "allow";
    bash = "allow";
    task = "allow";
    skill = "allow";
    lsp = "allow";
    todowrite = "allow";
    question = "allow";
    webfetch = "allow";
    websearch = "allow";
    external_directory = "allow";
    doom_loop = "allow";
  };

  opencodeGlobalSettings = {
    "$schema" = "https://opencode.ai/config.json";
    autoupdate = false;
    share = "manual";
    snapshot = true;

    model = defaultOpencodeModel;
    small_model = titleGenerationModel;
    default_agent = "build";
    subagent_depth = 2;

    instructions = [ "~/.config/opencode/AGENTS.md" ];

    permission = fullAccessPermissions;

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
      prune = true;
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
      batch_tool = true;
    };

    agent = {
      build = {
        mode = "primary";
        description = "Full-access coding agent with all tools enabled";
        variant = "max";
        permission = fullAccessPermissions;
      };
      plan = {
        mode = "primary";
        description = "Read-only architect that designs a change without editing files";
        variant = "max";
      };
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
