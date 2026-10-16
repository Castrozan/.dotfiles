{
  pkgs,
  lib,
  inputs,
  helpers,
  ...
}:
let
  configurations = import ./configurations.nix {
    inherit pkgs;
    homeManager = inputs.home-manager;
  };
  inherit (configurations) baseline configured customXdg;
  extensionId = "nngceckbapebfimnlniiiahkandclblb";
  manifestName =
    cfg:
    (
      if pkgs.stdenv.isDarwin then
        "Library/Application Support/Chromium"
      else
        "${cfg.xdg.configHome}/chromium"
    )
    + "/External Extensions/${extensionId}.json";
  manifest = configured.home.file.${manifestName configured};
  enabledFiles = cfg: lib.filterAttrs (_: file: file.enable) cfg.home.file;
  addedFiles = lib.subtractLists (builtins.attrNames (enabledFiles baseline)) (
    builtins.attrNames (enabledFiles configured)
  );
  expected = {
    external_update_url = "https://clients2.google.com/service/update2/crx";
  };
  packagePaths = cfg: map toString cfg.home.packages;
  checks = {
    package-is-null = {
      assertion =
        configured.programs.chromium.package == null
        && configured.programs.chromium.finalPackage == null
        && packagePaths configured == packagePaths baseline;
      message = "The extension module must add no browser or other package";
    };
    only-extension-file = {
      assertion =
        addedFiles == [ (manifestName configured) ]
        && builtins.fromJSON manifest.text == expected
        && !manifest.force;
      message = "Only the official external-extension manifest may be added, without overwriting an existing file";
    };
    existing-controls-preserved = {
      assertion =
        configured.programs.chromium.commandLineArgs == [ ]
        && configured.programs.chromium.nativeMessagingHosts == [ ]
        && configured.programs.chromium.dictionaries == [ ]
        && configured.xdg.desktopEntries == baseline.xdg.desktopEntries
        && configured.xdg.mimeApps.defaultApplications == baseline.xdg.mimeApps.defaultApplications
        && configured.home.sessionVariables == baseline.home.sessionVariables
        && builtins.attrNames configured.home.activation == builtins.attrNames baseline.home.activation;
      message = "The module must not add launcher, MIME, environment, native messaging or custom activation behavior";
    };
    platform-path = {
      assertion =
        manifest.target == (
          if pkgs.stdenv.isDarwin then
            "Library/Application Support/Chromium/External Extensions/${extensionId}.json"
          else
            ".config/chromium/External Extensions/${extensionId}.json"
        );
      message = "The manifest must use the pinned Home Manager platform path";
    };
    custom-xdg-path = {
      assertion =
        customXdg.home.file.${manifestName customXdg}.target == (
          if pkgs.stdenv.isDarwin then
            manifest.target
          else
            "configuration/chromium/External Extensions/${extensionId}.json"
        );
      message = "Linux XDG configHome must be honored without changing browser launch arguments";
    };
    package-conflict-refused = {
      assertion =
        !(builtins.tryEval (toString configurations.conflictingPackage.programs.chromium.package)).success;
      message = "An independently configured package must cause a conflict, not be silently replaced";
    };
    flags-conflict-refused = {
      assertion = !(builtins.tryEval configurations.conflictingFlags.programs.chromium.enable).success;
      message = "Pinned Home Manager must reject launcher flags with package=null";
    };
  };
in
(helpers.mkEvalCheckGroup "domain-browser-bitwarden" checks)
// {
  domain-browser-bitwarden-manifest-build =
    pkgs.runCommandLocal "check-domain-browser-bitwarden-manifest-build" { }
      ''
        cmp "${configured.home-files}/${manifest.target}" ${pkgs.writeText "expected-bitwarden.json" (builtins.toJSON expected)}
        touch "$out"
      '';
}
