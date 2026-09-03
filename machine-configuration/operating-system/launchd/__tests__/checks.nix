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
  testAgent = testConfiguration.launchd.agents.example;
  testPreservation = testConfiguration.home.activation."preserveRunningLaunchAgent-example";
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
}
