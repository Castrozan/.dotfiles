{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  pluginBundle = "/test/agent-plugin-bundle";
  hermesConfigTemplate = import ../config.nix {
    inherit pkgs pluginBundle;
  };
  hermesSoul = import ../soul.nix { inherit pkgs; };
  canonicalCore = builtins.readFile ../../../agent-instructions/core-rules/core.md;
  hermesIdentity = "You are Hermes Agent, an intelligent AI assistant created by Nous Research.";
  expectedHermesSoul = pkgs.writeText "expected-hermes-SOUL.md" "### Harness identity\n\n${hermesIdentity}\n\n${canonicalCore}";
  hermesHookCommandPath = "${pluginBundle}/plugin/native/hermes/hook-bridge";

  cfg = helpers.homeManagerTestConfiguration [
    ../.
    ../gateway.nix
  ];
  gatewayService = lib.mapAttrs (_: lib.toList) cfg.systemd.user.services.hermes-gateway.Service;
in
{
  domain-hermes-bin-wrapper =
    mkEvalCheck "domain-hermes-bin-wrapper" (builtins.hasAttr ".local/bin/hermes" cfg.home.file)
      ".local/bin/hermes should be in home.file";

  domain-hermes-generated-configuration =
    pkgs.runCommand "domain-hermes-generated-configuration"
      {
        nativeBuildInputs = [
          (import ../../../agent-instructions/instruction-projection.nix { inherit pkgs; }).python
        ];
      }
      ''
        python ${./verify-generated-configuration.py} ${hermesConfigTemplate} ${lib.escapeShellArg hermesHookCommandPath}
        touch "$out"
      '';

  domain-hermes-soul-carries-canonical-core =
    pkgs.runCommand "domain-hermes-soul-carries-canonical-core" { }
      ''
        cmp ${hermesSoul} ${expectedHermesSoul}
        touch "$out"
      '';

  domain-hermes-gateway-is-supervised-with-sudo-reachable =
    mkEvalCheck "domain-hermes-gateway-is-supervised-with-sudo-reachable"
      (
        lib.hasInfix "/bin/hermes gateway run --replace --external-supervisor" (
          lib.concatStrings gatewayService.ExecStart
        )
        && gatewayService.Restart == [ "always" ]
        && gatewayService.RestartPreventExitStatus == [ 78 ]
        && lib.hasInfix "/run/wrappers/bin" (lib.concatStrings gatewayService.Environment)
        && !(gatewayService ? NoNewPrivileges)
      )
      "The Hermes gateway must run under systemd supervision with the NixOS sudo wrapper on PATH and without NoNewPrivileges";
}
