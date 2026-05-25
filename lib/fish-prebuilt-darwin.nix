{ pkgs }:
let
  fetchPrebuiltBinary = import ./fetch-prebuilt-binary.nix { inherit pkgs; };
  version = "4.1.2";
in
fetchPrebuiltBinary {
  pname = "fish";
  inherit version;
  url = "https://github.com/fish-shell/fish-shell/releases/download/${version}/fish-${version}.app.zip";
  sha256 = "sha256-cTCvVrSjLQAhlZb2dDXXi6jbWaxxh/MQQGcRlhrnqvU=";
  archivePrefixToInstall = "fish-${version}.app/Contents/Resources/base/usr/local";
  preserveCodeSignature = true;
  meta = {
    description = "fish ${version} prebuilt darwin binary from upstream releases, preserves Apple code signature so macOS 26.1 (Tahoe) does not SIGKILL at exec";
    homepage = "https://fishshell.com/";
    license = pkgs.lib.licenses.gpl2Only;
    platforms = [
      "aarch64-darwin"
      "x86_64-darwin"
    ];
    mainProgram = "fish";
  };
}
