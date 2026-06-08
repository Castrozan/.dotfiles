{ lib }:
let
  isHookScriptFilename =
    filename:
    lib.hasSuffix ".py" filename || lib.hasSuffix ".sh" filename || lib.hasSuffix ".md" filename;

  isExcludedDirectoryName = directoryName: directoryName == "__pycache__" || directoryName == "tests";

  walkHooksDirectory =
    currentDirectory: relativePrefix:
    let
      directoryEntries = builtins.readDir currentDirectory;
      processEntry =
        entryName: entryType:
        let
          absolutePath = currentDirectory + "/${entryName}";
          relativePathToHooksRoot =
            if relativePrefix == "" then entryName else "${relativePrefix}/${entryName}";
        in
        if entryType == "directory" then
          if isExcludedDirectoryName entryName then
            [ ]
          else
            walkHooksDirectory absolutePath relativePathToHooksRoot
        else if entryType == "regular" && isHookScriptFilename entryName then
          [
            {
              inherit relativePathToHooksRoot;
              flatDeploymentFilename = entryName;
            }
          ]
        else
          [ ];
    in
    builtins.concatLists (lib.mapAttrsToList processEntry directoryEntries);
in
hooksRootDirectory: walkHooksDirectory hooksRootDirectory ""
