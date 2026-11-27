{
  pkgs,
  lib,
  config,
  ...
}:
let
  codex-unwrapped = import ./unwrapped.nix { inherit pkgs; };

  interactivePreferencesFile = import ../interactive-instructions.nix {
    inherit pkgs;
    inherit (config.home) homeDirectory;
  };

  profilePython = pkgs.python312.withPackages (pythonPackages: [ pythonPackages.tomli-w ]);

  interactiveProfile = pkgs.runCommand "dotfiles-interactive.config.toml" { } ''
    ${profilePython}/bin/python3 ${../scripts/generate_interactive_profile.py} \
      ${interactivePreferencesFile} "$out"
  '';

  profileSources = pkgs.writeText "codex-profile-sources.json" (
    builtins.toJSON { dotfiles-interactive = interactiveProfile; }
  );

  hookTrustExecutable = pkgs.writeShellScript "codex-approve-discovered-hooks" ''
    exec ${pkgs.python312}/bin/python3 ${../scripts/hook_trust}/approve.py "$@"
  '';

  sessionPython = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.tomlkit
    pythonPackages.websockets
  ]);

  sessionScripts = pkgs.runCommandLocal "codex-private-session-scripts" { } ''
    mkdir -p "$out"
    cp ${../scripts/session_server}/*.py "$out/"
    cp ${../scripts/hook_trust}/*.py "$out/"
    PYTHONPATH="$out" PYTHONDONTWRITEBYTECODE=1 ${sessionPython}/bin/python3 -c 'import launch_private_session'
  '';

  sessionExecutable = pkgs.writeShellScript "codex-private-session" ''
    exec ${sessionPython}/bin/python3 ${sessionScripts}/launch_private_session.py "$@"
  '';

  codex = pkgs.writeShellApplication {
    name = "codex";
    bashOptions = [ ];
    runtimeEnv = {
      NPM_CONFIG_PREFIX = "/nonexistent";
      CODEX_LAUNCHER_DEVELOPER_INSTRUCTIONS_FILE = "${interactivePreferencesFile}";
      CODEX_LAUNCHER_BINARY = "${codex-unwrapped}/bin/codex";
      CODEX_LAUNCHER_HOOK_TRUST_EXECUTABLE = "${hookTrustExecutable}";
      CODEX_LAUNCHER_SESSION_EXECUTABLE = "${sessionExecutable}";
    };
    text = builtins.readFile ../scripts/codex;
  };
in
{
  options.codex.unwrappedPackage = lib.mkOption {
    type = lib.types.package;
    default = codex-unwrapped;
    readOnly = true;
    description = "The bare upstream codex binary, without the interactive wrapper that selects the human's instruction profile and injects sandbox mode and approval policy. An autonomous harness builds its own full argv and must launch this, because re-passing a flag the wrapper already injected makes codex exit 2.";
  };

  config.home = {
    packages = [ codex ];
    activation.seedCodexProfilesAsMutableFiles = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
      ${profilePython}/bin/python3 ${../config}/seed_interactive_profiles.py "$HOME/.codex" ${profileSources}
    '';
    file = {
      ".codex/dotfiles-interactive.config.toml.nix-source".source = interactiveProfile;
      ".local/bin/codex".source = "${codex}/bin/codex";
    };
  };
}
