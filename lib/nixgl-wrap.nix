{
  pkgs,
  inputs,
  isNixOS,
}:
let
  nixglSystem = pkgs.stdenv.hostPlatform.system;

  wrapBinariesWithGLPackage =
    glWrapperPackage: glBinaryName:
    {
      package,
      binaries,
    }:
    if isNixOS then
      package
    else
      let
        wrappedBinaries = map (
          binaryName:
          pkgs.writeShellScriptBin binaryName ''
            exec ${glWrapperPackage}/bin/${glBinaryName} ${package}/bin/${binaryName} "$@"
          ''
        ) binaries;
      in
      pkgs.symlinkJoin {
        name = "${package.pname or package.name}-wrapped";
        paths = wrappedBinaries ++ [ package ];
      };
in
{
  wrapWithNixGLIntel =
    wrapBinariesWithGLPackage inputs.nixgl.packages.${nixglSystem}.nixGLIntel
      "nixGLIntel";

  wrapWithNixVulkanIntel =
    wrapBinariesWithGLPackage inputs.nixgl.packages.${nixglSystem}.nixVulkanIntel
      "nixVulkanIntel";
}
