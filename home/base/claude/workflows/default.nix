_:
let
  workflowFilesFromInstall =
    install:
    builtins.listToAttrs (
      map (workflowFileName: {
        name = ".claude/workflows/${workflowFileName}";
        value.source = install.workflowSources.${workflowFileName};
      }) (builtins.attrNames install.workflowSources)
    );

  housekeepingInstall = import ../../../../agents/skills/housekeeping/install { };
  pageComposerInstall = import ../../../../agents/skills/page-composer/install { };
in
{
  home.file =
    workflowFilesFromInstall housekeepingInstall
    // workflowFilesFromInstall pageComposerInstall
    // {
      ".claude/workflows/dotfiles-change-review.js".source = ./dotfiles-change-review.js;
    };
}
