{
  lib,
  mkEvalCheck,
}:
let
  listHookScriptsRecursively = import ../../../hooks/list-hook-scripts-recursively.nix {
    inherit lib;
  };

  allHookScriptsAcrossSubdirectories = listHookScriptsRecursively ../../../../agent-harness/hooks/runtime;

  sourcePathsByFlatDeploymentFilename = builtins.groupBy (
    entry: entry.flatDeploymentFilename
  ) allHookScriptsAcrossSubdirectories;

  collidingFlatDeploymentFilenames = lib.filterAttrs (
    _: entries: lib.length entries > 1
  ) sourcePathsByFlatDeploymentFilename;

  describeCollision =
    flatDeploymentFilename: entries:
    "${flatDeploymentFilename} <- "
    + lib.concatStringsSep " and " (map (entry: entry.relativePathToHooksRoot) entries);
in
{
  hooks-flat-deploy-excludes-the-human-communication-policy =
    mkEvalCheck "hooks-flat-deploy-excludes-the-human-communication-policy"
      (!(builtins.hasAttr "interactive-communication.md" sourcePathsByFlatDeploymentFilename))
      "the hook package must carry enforcement only; interactive communication guidance ships as a side file in the humanize skill package";

  hooks-flat-deploy-has-no-basename-collision =
    mkEvalCheck "hooks-flat-deploy-has-no-basename-collision" (collidingFlatDeploymentFilenames == { })
      (
        "the hook deploy flattens every nested script into one directory keyed by basename, so two "
        + "files sharing a basename silently overwrite each other and which one survives depends on "
        + "readDir ordering; the losing hook disappears with no build error. Rename one side, or nest "
        + "the shared name behind a directory-qualified filename. Colliding basenames: "
        + lib.concatStringsSep "; " (lib.mapAttrsToList describeCollision collidingFlatDeploymentFilenames)
      );
}
