{
  helpers,
  lib,
  pkgs,
  ...
}:
let
  testConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    (
      {
        config,
        lib,
        pkgs,
        ...
      }:
      let
        rebuildSafeLaunchAgentLib = import ../rebuild-safe-launch-agent-library.nix {
          inherit config lib pkgs;
        };
      in
      rebuildSafeLaunchAgentLib.mkRebuildSafeLaunchAgent {
        name = "example";
        label = "com.dotfiles.example";
        package = pkgs.hello;
        executableName = "hello";
        programArguments = [ "--greeting=hello" ];
        serviceConfig = {
          KeepAlive = true;
          RunAtLoad = true;
        };
      }
    )
  ];
  restartingConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    (
      {
        config,
        lib,
        pkgs,
        ...
      }:
      (import ../rebuild-safe-launch-agent-library.nix { inherit config lib pkgs; })
      .mkRebuildSafeLaunchAgent
        {
          name = "example";
          label = "com.dotfiles.example";
          package = pkgs.hello;
          executableName = "hello";
          restartWhenPackageChanges = true;
          serviceConfig.KeepAlive = true;
        }
    )
  ];
  testAgent = testConfiguration.launchd.agents.example;
  testPreservation = testConfiguration.home.activation."preserveRunningLaunchAgent-example";
  testRestart = restartingConfiguration.home.activation."restartLaunchAgentOnNewPackage-example";
  recordingLaunchctl = pkgs.writeShellScriptBin "launchctl" ''
    printf '%s\n' "$*" >> "$LAUNCHCTL_INVOCATIONS"
    test "$1" != print || test -z "''${AGENT_UNLOADED:-}"
  '';
  restartScript = ../scripts/restart-launch-agent-on-new-package.sh;
  fakeLaunchctl = pkgs.writeShellScriptBin "launchctl" ''
    test "$1" = print
    printf 'program = %s/bin/example\n' ${pkgs.hello}
  '';
  fakeNixStore = pkgs.writeShellScriptBin "nix-store" ''
    printf '%s\n' "$*" >> "$NIX_STORE_INVOCATIONS"
  '';
  inactiveLaunchctl = pkgs.writeShellScriptBin "launchctl" ''
    exit 1
  '';
in
{
  domain-operating-system-rebuild-safe-launch-agent-uses-stable-profile-path =
    helpers.mkEvalCheck "domain-operating-system-rebuild-safe-launch-agent-uses-stable-profile-path"
      (
        lib.hasSuffix "/bin/example-rebuild-safe-launcher" (builtins.head testAgent.config.ProgramArguments)
        && !(lib.hasPrefix "/nix/store/" (builtins.head testAgent.config.ProgramArguments))
        && builtins.elem "--greeting=hello" testAgent.config.ProgramArguments
        && testAgent.config.Label == "com.dotfiles.example"
        && testAgent.config.KeepAlive
        && builtins.elem "writeBoundary" testPreservation.after
        && builtins.elem "setupLaunchAgents" testPreservation.before
      )
      "the constructor must keep the plist independent from generation-specific store paths and preserve loaded jobs before Home Manager reloads agents";

  domain-operating-system-rebuild-safe-launch-agent-preserves-loaded-job =
    pkgs.runCommandLocal "check-domain-operating-system-rebuild-safe-launch-agent-preserves-loaded-job"
      { }
      ''
        mkdir -p source destination roots
        printf 'new plist' >source/com.dotfiles.example.plist
        printf 'old plist' >destination/com.dotfiles.example.plist
        export NIX_STORE_INVOCATIONS=$PWD/nix-store-invocations
        export PATH=${fakeLaunchctl}/bin:${fakeNixStore}/bin:${pkgs.coreutils}/bin:${pkgs.diffutils}/bin:${pkgs.gnugrep}/bin
        ${pkgs.bash}/bin/bash ${../scripts/preserve-running-launch-agent.sh} com.dotfiles.example source/com.dotfiles.example.plist destination/com.dotfiles.example.plist roots
        cmp source/com.dotfiles.example.plist destination/com.dotfiles.example.plist
        grep -qF '${pkgs.hello} --add-root roots/${builtins.baseNameOf (toString pkgs.hello)} --indirect' "$NIX_STORE_INVOCATIONS"
        touch $out
      '';

  domain-operating-system-rebuild-safe-launch-agent-defers-inactive-job-to-home-manager =
    pkgs.runCommandLocal
      "check-domain-operating-system-rebuild-safe-launch-agent-defers-inactive-job-to-home-manager"
      { }
      ''
        mkdir -p source destination roots
        printf 'new plist' >source/com.dotfiles.example.plist
        printf 'old plist' >destination/com.dotfiles.example.plist
        export PATH=${inactiveLaunchctl}/bin:${pkgs.coreutils}/bin:${pkgs.diffutils}/bin:${pkgs.gnugrep}/bin
        ${pkgs.bash}/bin/bash ${../scripts/preserve-running-launch-agent.sh} com.dotfiles.example source/com.dotfiles.example.plist destination/com.dotfiles.example.plist roots
        grep -qxF 'old plist' destination/com.dotfiles.example.plist
        touch $out
      '';

  domain-operating-system-rebuild-safe-launch-agent-restarts-only-when-asked =
    helpers.mkEvalCheck "domain-operating-system-rebuild-safe-launch-agent-restarts-only-when-asked"
      (
        !(testConfiguration.home.activation ? "restartLaunchAgentOnNewPackage-example")
        && builtins.elem "setupLaunchAgents" testRestart.after
        && lib.hasInfix (builtins.unsafeDiscardStringContext "/rebuild-safe-launch-agents/example/${builtins.baseNameOf (toString pkgs.hello)}") (
          builtins.unsafeDiscardStringContext testRestart.data
        )
      )
      "an agent restarts on a new package only when it asks to, after Home Manager loads agents, and checks the new package's runtime root";

  domain-operating-system-rebuild-safe-launch-agent-restarts-in-place-on-new-package =
    pkgs.runCommandLocal
      "check-domain-operating-system-rebuild-safe-launch-agent-restarts-in-place-on-new-package"
      { }
      ''
        export LAUNCHCTL_INVOCATIONS=$PWD/launchctl-invocations
        export PATH=${recordingLaunchctl}/bin:${pkgs.coreutils}/bin:${pkgs.gnugrep}/bin
        touch "$LAUNCHCTL_INVOCATIONS"
        ${pkgs.bash}/bin/bash ${restartScript} com.dotfiles.example roots/new-package
        grep -qxF "kickstart -k gui/$(id -u)/com.dotfiles.example" "$LAUNCHCTL_INVOCATIONS"
        if grep -qE '^(bootout|bootstrap)' "$LAUNCHCTL_INVOCATIONS"; then exit 1; fi

        : >"$LAUNCHCTL_INVOCATIONS"
        mkdir roots
        ln -s /nonexistent roots/new-package
        ${pkgs.bash}/bin/bash ${restartScript} com.dotfiles.example roots/new-package
        if grep -q kickstart "$LAUNCHCTL_INVOCATIONS"; then exit 1; fi

        : >"$LAUNCHCTL_INVOCATIONS"
        AGENT_UNLOADED=1 ${pkgs.bash}/bin/bash ${restartScript} com.dotfiles.example roots/other-package
        if grep -q kickstart "$LAUNCHCTL_INVOCATIONS"; then exit 1; fi
        touch $out
      '';
}
