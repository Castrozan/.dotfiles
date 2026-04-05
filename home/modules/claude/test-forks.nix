{
  config,
  pkgs,
  lib,
  ...
}:
let
  homeDir = config.home.homeDirectory;
  testForksBase = "${homeDir}/.claude/test-forks";
  personalSkillSetDirectory = "${homeDir}/.local/share/claude-skill-sets/personal";

  bunBin = "${homeDir}/.bun/bin";

  # mcx requires bun >= 1.3.11 (nixpkgs 1.3.3 segfaults).
  # Use ~/.bun/bin/bun installed via bun.sh official installer.
  installMcxCli = pkgs.writeShellScript "install-mcx-cli" ''
    set -euo pipefail
    export PATH="${bunBin}:$PATH"

    if [ ! -x "${bunBin}/bun" ]; then
      echo "mcx: bun not found at ${bunBin}/bun — install via: curl -fsSL https://bun.sh/install | bash"
      exit 0
    fi

    if [ ! -x "${bunBin}/mcx" ]; then
      ${bunBin}/bun add -g @papicandela/mcx-cli
    fi

    if [ ! -d "${homeDir}/.mcx" ]; then
      ${bunBin}/mcx init
    fi
  '';

  testForks = {
    mcx = {
      description = "MCX (Modular Code Execution) sandbox";
      mcpServers = {
        mcx = {
          command = "${bunBin}/mcx";
          args = [ "serve" ];
        };
      };
      claudeMd = ''
        # MCX Test Fork

        Isolated test environment for [MCX](https://github.com/schizoidcock/mcx).
        MCX replaces direct tool calls with code execution in a Bun sandbox.

        Use `mcx_execute`, `mcx_search`, etc. via the mcx MCP server.
        To generate adapters from OpenAPI specs: `mcx gen ./api-docs.md -n myapi`
      '';
      extraPackages = [ ];
    };
  };

  generateFishFunction =
    name: fork:
    let
      workspaceDir = "${testForksBase}/${name}";
    in
    ''
      function claude-${name} --description "${fork.description}"
        cd ${workspaceDir} && command claude --add-dir ${personalSkillSetDirectory} $argv
      end
    '';

  allFishFunctions = lib.concatStringsSep "\n" (lib.mapAttrsToList generateFishFunction testForks);

  generateWorkspaceActivation =
    name: fork:
    let
      workspaceDir = "${testForksBase}/${name}";
      mcpJsonFile = pkgs.writeText "test-fork-${name}-mcp.json" (
        builtins.toJSON { mcpServers = fork.mcpServers; }
      );
      claudeMdFile = pkgs.writeText "test-fork-${name}-claude.md" fork.claudeMd;
    in
    ''
      mkdir -p "${workspaceDir}/.claude"
      cp --no-preserve=mode ${mcpJsonFile} "${workspaceDir}/.mcp.json"

      if [ ! -f "${workspaceDir}/CLAUDE.md" ]; then
        cp --no-preserve=mode ${claudeMdFile} "${workspaceDir}/CLAUDE.md"
      fi
    '';

  allWorkspaceActivations = lib.concatStringsSep "\n" (
    lib.mapAttrsToList generateWorkspaceActivation testForks
  );

  allExtraPackages = lib.concatMap (fork: fork.extraPackages or [ ]) (lib.attrValues testForks);
in
{
  xdg.configFile."fish/conf.d/claude-test-forks.fish".text = allFishFunctions;

  home = {
    packages = allExtraPackages;

    activation.installMcxCli = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${installMcxCli}
    '';

    activation.createTestForkWorkspaces = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      ${allWorkspaceActivations}
    '';
  };
}
