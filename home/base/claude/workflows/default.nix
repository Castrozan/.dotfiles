_:
let
  housekeepingInstall = import ../../../../agents/skills/housekeeping/install { };

  housekeepingWorkflowFiles = builtins.listToAttrs (
    map (workflowFileName: {
      name = ".claude/workflows/${workflowFileName}";
      value.source = housekeepingInstall.workflowSources.${workflowFileName};
    }) (builtins.attrNames housekeepingInstall.workflowSources)
  );
in
{
  home.file = housekeepingWorkflowFiles // {
    ".claude/workflows/dotfiles-change-review.js".source = ./dotfiles-change-review.js;
  };
}
