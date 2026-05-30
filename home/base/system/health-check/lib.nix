{ lib }:
rec {
  mkBinaryProbe =
    {
      category ? "bin",
      name,
      command,
    }:
    {
      inherit category name;
      probe = "${command} >/dev/null 2>&1";
    };

  mkProcessProbe =
    {
      category ? "daemon",
      name,
      pattern,
    }:
    {
      inherit category name;
      probe = "pgrep -f ${lib.escapeShellArg pattern} >/dev/null 2>&1";
    };

  mkAppProbe =
    {
      category ? "app",
      name,
      bundle,
    }:
    {
      inherit category name;
      probe = ''
        for candidateDirectory in /Applications "$HOME/Applications" "$HOME/Applications/Home Manager Apps"; do
          if [ -d "$candidateDirectory/${bundle}.app" ]; then
            exit 0
          fi
        done
        if find /nix/store -maxdepth 5 -type d -name ${lib.escapeShellArg "${bundle}.app"} -print -quit 2>/dev/null | grep -q .; then
          exit 0
        fi
        exit 1
      '';
    };

  mkFileProbe =
    {
      category ? "config",
      name,
      path,
      contains ? null,
    }:
    {
      inherit category name;
      probe =
        if contains == null then
          "test -s ${lib.escapeShellArg path}"
        else
          "test -s ${lib.escapeShellArg path} && grep -qF ${lib.escapeShellArg contains} ${lib.escapeShellArg path}";
    };

  mkLaunchdProbe =
    {
      category ? "daemon",
      name,
      label,
    }:
    {
      inherit category name;
      probe = "launchctl list ${lib.escapeShellArg label} 2>/dev/null | grep -q '\"PID\" ='";
    };

  mkSystemdUserUnitProbe =
    {
      category ? "daemon",
      name,
      unit,
    }:
    {
      inherit category name;
      probe = "systemctl --user is-active --quiet ${lib.escapeShellArg unit}";
    };
}
