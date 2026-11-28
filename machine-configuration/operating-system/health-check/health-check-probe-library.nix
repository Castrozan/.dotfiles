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
      applicableWhen ? null,
    }:
    {
      inherit category name applicableWhen;
      probe = "pgrep -f ${lib.escapeShellArg pattern} >/dev/null 2>&1";
    };

  mkCommandProbe =
    {
      category ? "daemon",
      name,
      command,
      applicableWhen ? null,
    }:
    {
      inherit category name applicableWhen;
      probe = "${command} >/dev/null 2>&1";
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
