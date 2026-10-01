{
  lib,
  hostname,
  localWrapperRepoPath,
}:
{
  machineLocalWrapperDirective = lib.optionalString (localWrapperRepoPath != null) (
    "\n"
    + lib.replaceStrings [ "@hostname@" "@localWrapperRepoPath@" ] [ hostname localWrapperRepoPath ] (
      builtins.readFile ./machine-local-wrapper-instructions.md
    )
  );
  repoCiToolingDirective = "\n" + builtins.readFile ./repository-ci-instructions.md;
  repoActivationDirective = lib.optionalString (hostname == "rin") (
    "\n" + builtins.readFile ./repository-activation-instructions.md
  );
}
