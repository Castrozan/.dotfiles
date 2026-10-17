{
  config,
  pkgs,
  ...
}:
let
  contextModePackage = import ./package.nix { inherit pkgs; };
  contextModeDependencies = "${contextModePackage}/lib/context-mode/node_modules";
  contextModeRuntime = pkgs.writeShellScript "context-mode-runtime" ''
    umask 077
    contextModeStateDirectory="''${XDG_STATE_HOME:-${config.xdg.stateHome}}/context-mode"
    mkdir -p "$contextModeStateDirectory"
    export CONTEXT_MODE_DIR="$contextModeStateDirectory/data"
    export CLAUDE_CONFIG_DIR="$contextModeStateDirectory/claude"
    export XDG_CONFIG_HOME="$contextModeStateDirectory/config"
    export CONTEXT_MODE_PLATFORM=claude-code
    export PATH="${
      pkgs.lib.makeBinPath [
        pkgs.bun
        pkgs.nodejs_22
        pkgs.python312
        pkgs.bash
      ]
    }:$PATH"
    exec ${pkgs.bun}/bin/bun "$@"
  '';

  contextModePlugin =
    pkgs.runCommand "context-mode-claude-plugin-${contextModePackage.version}" { }
      ''
        mkdir -p "$out"
        cp -R ${contextModeDependencies}/context-mode/. "$out/"
        chmod -R u+w "$out"
        ln -s ${contextModeDependencies} "$out/node_modules"
        ${pkgs.python312}/bin/python3 ${./scripts/configure_plugin.py} "$out" ${contextModeRuntime}
      '';

  contextModeCommand = pkgs.writeShellScriptBin "context-mode" ''
    exec ${contextModeRuntime} ${contextModePlugin}/cli.bundle.mjs "$@"
  '';

  claudeContextModeCommand = pkgs.writeShellScriptBin "claude-context-mode" ''
    exec ${config.claude.package}/bin/claude --plugin-dir ${contextModePlugin} "$@"
  '';
in
{
  home.packages = [
    contextModeCommand
    claudeContextModeCommand
  ];

  home.file.".local/share/claude-context-mode".source = contextModePlugin;
}
