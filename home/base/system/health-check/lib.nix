{ lib }:
# health-check answers "is it working right now?", not "is it installed?".
# Prefer probes that exercise runtime function:
#   - liveness  : process / launchd / systemd unit currently running
#   - functional: a command that fails if config/auth/wiring is broken
# Plain "does the binary exist" / "is the .app bundle present" probes only
# prove deployment - keep those out of healthCheck.probes and rely on
# rebuild verification instead.
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
