{
  pkgs,
  lib,
  ...
}:
let
  pmAdapterInstructions = builtins.readFile ./instructions/pm-runtime.md;

  seedPmWorkspaceScript = pkgs.writeShellScript "seed-one-workspace-pm" (
    builtins.readFile ./scripts/seed-pm-workspace.sh
  );
in
{
  options.clawde.agents = lib.mkOption {
    type = lib.types.attrsOf (
      lib.types.submodule {
        options.channel.pm = lib.mkOption {
          type = lib.types.submodule {
            options.projectDirectory = lib.mkOption {
              type = lib.types.nullOr lib.types.str;
              default = null;
              description = "Absolute path to the project directory the PM agent owns. Becomes the agent workspace; state lives at <projectDirectory>/.pm/HEARTBEAT.md.";
            };
          };
          default = { };
          description = "PM adapter-specific options. Used only when channel.type = 'pm'.";
        };
      }
    );
  };

  config = {
    clawde.channelAdapters.pm = {
      instructions = pmAdapterInstructions;
      workspaceDirectoryFor = agent: agent.channel.pm.projectDirectory;
      agentActivationScriptFor =
        { workspaceDirectory, ... }: "${seedPmWorkspaceScript} ${lib.escapeShellArg workspaceDirectory}";
    };
  };
}
