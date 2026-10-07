{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;

  codexGlobalInstructions =
    (import ../../codex/global-instructions.nix { config = cfg; }).home.file.".codex/AGENTS.md".source;
  piGlobalInstructions =
    pkgs.writeText "pi-global-instructions.md"
      cfg.home.file.".pi/agent/AGENTS.md".text;
  loaders = import ../plugin-loaders { inherit pkgs; };
in
{
  domain-pi-bash-output-recovery = pkgs.runCommand "domain-pi-bash-output-recovery" { } ''
    ${pkgs.nodejs_22}/bin/node ${./verify-bash-output-recovery.mjs} \
      ${loaders}/node_modules \
      ${cfg.home.file.".pi/agent/extensions/bash-output-recovery.js".source}
    touch "$out"
  '';

  domain-pi-workflow-extensions = pkgs.runCommand "domain-pi-workflow-extensions" { } ''
    ${pkgs.nodejs_22}/bin/node ${./verify-workflow-extensions.mjs} \
      ${loaders}/node_modules \
      ${cfg.home.file.".pi/agent/extensions/loop-guard".source} \
      ${cfg.home.file.".pi/loop-guard.json".source}
    touch "$out"
  '';

  domain-pi-native-plugin-registration = pkgs.runCommand "domain-pi-native-plugin-registration" { } ''
    ${pkgs.nodejs_22}/bin/node ${./verify-registration.mjs} \
      ${import ../plugin-loaders { inherit pkgs; }}/node_modules \
      ${../scripts/register-managed-plugin.mjs}
    touch "$out"
  '';

  domain-pi-package =
    mkEvalCheck "domain-pi-package" (hasPackageMatching "pi")
      "the Pi module must install its wrapped native executable";

  domain-pi-bin-wrapper =
    mkEvalCheck "domain-pi-bin-wrapper" (builtins.hasAttr ".local/bin/pi" cfg.home.file)
      ".local/bin/pi should be in home.file, matching how every other agent harness here is reachable by an absolute path";

  domain-pi-installed-package-is-the-wrapper =
    mkEvalCheck "domain-pi-installed-package-is-the-wrapper" (cfg.pi.package.name == "pi")
      "the upstream release unpacks to a directory of sidecar assets around a Bun executable and carries no bin/, so installing it raw would put nothing on PATH. Only the wrapper exposes a `pi` binary";

  domain-pi-global-instructions-carry-the-same-core-rules-as-every-other-harness =
    pkgs.runCommand "domain-pi-global-instructions-carry-the-same-core-rules-as-every-other-harness" { }
      ''
        cmp ${piGlobalInstructions} ${codexGlobalInstructions}
        touch "$out"
      '';
}
