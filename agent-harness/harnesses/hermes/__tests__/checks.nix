{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  pluginDirectory = "/test/.hermes/plugins/dotfiles";
  hermesConfigTemplate = import ../config.nix {
    inherit pkgs pluginDirectory;
  };
  hermesSoul = import ../soul.nix { inherit pkgs; };
  canonicalCore = builtins.readFile ../../../agent-instructions/core-rules/core.md;
  hermesIdentity = "You are Hermes Agent, an intelligent AI assistant created by Nous Research.";
  expectedHermesSoul = pkgs.writeText "expected-hermes-SOUL.md" "### Harness identity\n\n${hermesIdentity}\n\n${canonicalCore}";
  hermesHookCommandPath = "${pluginDirectory}/native/hermes/hook-bridge";

  cfg = helpers.homeManagerTestConfiguration [
    ../.
    ../gateway.nix
  ];
  gatewayService = lib.mapAttrs (_: lib.toList) cfg.systemd.user.services.hermes-agent.Service;

  discordBotCfg = helpers.homeManagerTestConfiguration [
    ../.
    ../gateway.nix
    {
      hermes.discordBots.test-bot = {
        botTokenSecretName = "discord-bot-token-test";
        allowedDiscordUserId = "42";
      };
    }
  ];
  discordBotProvisioning = lib.concatStringsSep "\n" (
    lib.toList discordBotCfg.systemd.user.services.hermes-agent.Service.ExecStartPre
  );
in
{
  domain-hermes-bin-wrapper =
    mkEvalCheck "domain-hermes-bin-wrapper" (builtins.hasAttr ".local/bin/hermes" cfg.home.file)
      ".local/bin/hermes should be in home.file";

  domain-hermes-runtime-carries-discord-voice-receiver =
    pkgs.runCommand "domain-hermes-runtime-carries-discord-voice-receiver" { }
      ''
        HOME=$TMPDIR ${cfg.hermes.unwrappedPackage.hermesVenv}/bin/python3 -c \
          'import davey; from plugins.platforms.discord.adapter import VoiceReceiver; VoiceReceiver.check_silence'
        touch "$out"
      '';

  domain-hermes-runtime-supports-the-discord-voice-bridge-listener =
    pkgs.runCommand "domain-hermes-runtime-supports-the-discord-voice-bridge-listener" { }
      ''
        HOME=$TMPDIR \
        PYTHONPATH=${../../clawde/discord/voice-bridge/scripts}:${../../../../machine-configuration/media/avatar/scripts/listening} \
          ${cfg.hermes.unwrappedPackage.hermesVenv}/bin/python3 \
          ${../../clawde/discord/voice-bridge/__tests__/verify-listener-receiver-credentials.py}
        HOME=$TMPDIR \
        PYTHONPATH=${../../clawde/discord/voice-bridge/scripts}:${../../../../machine-configuration/media/avatar/scripts/listening} \
          ${cfg.hermes.unwrappedPackage.hermesVenv}/bin/python3 \
          ${../../clawde/discord/voice-bridge/__tests__/verify-speech-transcription-contract.py} \
          ${pkgs.ffmpeg}/bin/ffmpeg
        touch "$out"
      '';

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

  domain-hermes-launcher-survives-instruction-changes =
    pkgs.runCommand "domain-hermes-launcher-survives-instruction-changes"
      {
        exportReferencesGraph = [
          "launcherClosure"
          cfg.hermes.package
        ];
      }
      ''
        grep -qFe ${builtins.unsafeDiscardStringContext cfg.agentPlugins.bundle} -e hermes-SOUL launcherClosure && exit 1
        touch "$out"
      '';

  domain-hermes-soul-carries-canonical-core =
    pkgs.runCommand "domain-hermes-soul-carries-canonical-core" { }
      ''
        cmp ${hermesSoul} ${expectedHermesSoul}
        touch "$out"
      '';

  domain-hermes-opts-out-of-bundled-skills =
    mkEvalCheck "domain-hermes-opts-out-of-bundled-skills"
      (builtins.hasAttr ".hermes/.no-bundled-skills" cfg.home.file)
      "Hermes must carry only the dotfiles skills, so the bundled skill opt-out marker must be deployed";

  domain-hermes-reaches-claude-through-the-official-subscription-plugin =
    pkgs.runCommand "domain-hermes-reaches-claude-through-the-official-subscription-plugin" { }
      ''
        grep -q '^kind: model-provider$' ${
          cfg.home.file.".hermes/plugins/claude-subscription-directsdk".source
        }/plugin.yaml
        touch "$out"
      '';

  domain-hermes-gateway-does-not-use-the-unit-name-hermes-rewrites =
    mkEvalCheck "domain-hermes-gateway-does-not-use-the-unit-name-hermes-rewrites"
      (!(builtins.hasAttr "hermes-gateway" cfg.systemd.user.services))
      "Hermes rewrites hermes-gateway.service on restart, which fails against a Nix-owned read-only unit";

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

  domain-hermes-gateway-provisions-each-discord-bot-profile =
    mkEvalCheck "domain-hermes-gateway-provisions-each-discord-bot-profile"
      (
        lib.hasInfix "%h/.hermes/profiles/test-bot/.env %h/.secrets/discord-bot-token-test 42" discordBotProvisioning
        && lib.hasInfix "HERMES_HOME=%h/.hermes/profiles/test-bot " discordBotProvisioning
        && builtins.hasAttr ".hermes/profiles/test-bot/plugins/dotfiles" discordBotCfg.home.file
        && builtins.hasAttr ".hermes/profiles/test-bot/.no-bundled-skills" discordBotCfg.home.file
        &&
          lib.hasInfix "\"gateway_restart_notification\":false"
            discordBotCfg.home.file.".hermes/profiles/test-bot/gateway.json".text
      )
      "Every declared Discord bot must get its environment, seeded configuration, plugins, skill opt-out and restart silence before the gateway starts";
}
