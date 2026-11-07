{
  pkgs,
  lib,
  config,
  ...
}:
let
  workflowFilesFromInstall =
    install:
    builtins.listToAttrs (
      map (workflowFileName: {
        name = ".claude/workflows/${workflowFileName}";
        value.source = "${config.agentPlugins.bundle}/plugin/workflows/${workflowFileName}";
      }) (builtins.attrNames install.workflowSources)
    );

  localWorkflowsDirectory = ./.;
  localWorkflowFileNames = builtins.filter (fileName: lib.hasSuffix ".js" fileName) (
    builtins.attrNames (builtins.readDir localWorkflowsDirectory)
  );
  localWorkflowFiles = builtins.listToAttrs (
    map (fileName: {
      name = ".claude/workflows/${fileName}";
      value.source = "${config.agentPlugins.bundle}/plugin/workflows/${fileName}";
    }) localWorkflowFileNames
  );

  pageComposerInstall = import ../../../agent-instructions/skills/writing/page-composer/install { };

  housekeepingSlicesCommand = pkgs.writeShellScriptBin "dotfiles-housekeeping-slices" ''
    export PATH="${lib.makeBinPath [ pkgs.git ]}:$PATH"
    exec ${pkgs.python312}/bin/python3 ${./scripts/dotfiles_housekeeping_slices.py} "$@"
  '';
in
{
  home.file = localWorkflowFiles // workflowFilesFromInstall pageComposerInstall;
  home.packages = [ housekeepingSlicesCommand ];
}
