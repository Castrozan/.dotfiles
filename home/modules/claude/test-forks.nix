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

  testForks = {
    mcx = {
      description = "MCX (Modular Code Execution) sandbox";
      mcpServers = {
        mcx = {
          command = "mcx";
          args = [ "serve" ];
        };
      };
      claudeMd = ''
        # MCX Test Fork

        Isolated test environment for [MCX](https://github.com/schizoidcock/mcx).
        MCX replaces direct tool calls with code execution in a Bun sandbox.

        ## Setup (first time)
        ```
        bun add -g @papicandela/mcx-cli
        mcx init
        ```

        ## Usage
        The `mcx` MCP server is configured in `.mcp.json`. Use `mcx_execute`, `mcx_search`, etc.
        To generate adapters from OpenAPI specs: `mcx gen ./api-docs.md -n myapi`
      '';
      extraPackages = [ pkgs.bun ];
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

    activation.createTestForkWorkspaces = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      ${allWorkspaceActivations}
    '';
  };
}
