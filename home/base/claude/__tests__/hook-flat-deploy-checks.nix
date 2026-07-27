{
  lib,
  mkEvalCheck,
}:
let
  listHookScriptsRecursively = import ../../agent-hooks/list-hook-scripts-recursively.nix {
    inherit lib;
  };

  allHookScriptsAcrossSubdirectories = listHookScriptsRecursively ../../../../agents/hooks;

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
