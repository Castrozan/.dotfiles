{ lib, config, ... }:
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
in
{
  home.file = localWorkflowFiles // workflowFilesFromInstall pageComposerInstall;
}
