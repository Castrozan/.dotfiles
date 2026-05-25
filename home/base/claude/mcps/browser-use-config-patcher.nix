{
  browserUseConfigDir,
  chromeBinary,
}:
{ pkgs, lib, ... }:
let
  defaultProfileId = "nix-default";
  defaultConfig = builtins.toJSON {
    browser_profile = {
      "${defaultProfileId}" = {
        id = defaultProfileId;
        default = true;
        headless = false;
        executable_path = chromeBinary;
      };
    };
  };
  defaultConfigFile = pkgs.writeText "browseruse-default-config.json" defaultConfig;
  patchBrowserUseConfigWithChromeBinary = pkgs.writeShellScript "patch-browseruse-config-with-chrome-binary" ''
    set -euo pipefail
    CONFIG="${browserUseConfigDir}/config.json"
    mkdir -p "${browserUseConfigDir}"
    if [ ! -f "$CONFIG" ] || [ "$(${pkgs.jq}/bin/jq '.browser_profile | length' "$CONFIG" 2>/dev/null)" = "0" ] || [ "$(${pkgs.jq}/bin/jq '.browser_profile | length' "$CONFIG" 2>/dev/null)" = "null" ]; then
      cp --no-preserve=mode ${defaultConfigFile} "$CONFIG"
    else
      ${pkgs.jq}/bin/jq '
        .browser_profile |= (
          to_entries |
          map(.value.executable_path = "${chromeBinary}" | .value.headless = false) |
          from_entries
        )
      ' "$CONFIG" | ${pkgs.moreutils}/bin/sponge "$CONFIG"
    fi
  '';
in
{
  home.activation.writeBrowserUseConfig = lib.mkIf pkgs.stdenv.hostPlatform.isLinux (
    lib.hm.dag.entryAfter [ "writeBoundary" ] ''
      run ${patchBrowserUseConfigWithChromeBinary}
    ''
  );
}
