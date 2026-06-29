{ lib, ... }:
let
  workflowFilesFromInstall =
    install:
    builtins.listToAttrs (
      map (workflowFileName: {
        name = ".claude/workflows/${workflowFileName}";
        value.source = install.workflowSources.${workflowFileName};
      }) (builtins.attrNames install.workflowSources)
    );

  localWorkflowsDirectory = ./.;
  localWorkflowFileNames = builtins.filter (fileName: lib.hasSuffix ".js" fileName) (
    builtins.attrNames (builtins.readDir localWorkflowsDirectory)
  );
  localWorkflowFiles = builtins.listToAttrs (
    map (fileName: {
      name = ".claude/workflows/${fileName}";
      value.source = localWorkflowsDirectory + "/${fileName}";
    }) localWorkflowFileNames
  );

  housekeepingInstall = import ../../../../agents/skills/housekeeping/install { };
  pageComposerInstall = import ../../../../agents/skills/page-composer/install { };
in
{
  home.file =
    localWorkflowFiles
    // workflowFilesFromInstall housekeepingInstall
    // workflowFilesFromInstall pageComposerInstall;
}
