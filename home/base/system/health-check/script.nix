{
  pkgs,
  lib,
  probes,
}:
let
  renderProbeCall =
    probe:
    lib.concatStringsSep " " [
      "runProbe"
      (lib.escapeShellArg probe.category)
      (lib.escapeShellArg probe.name)
      (lib.escapeShellArg probe.probe)
      (lib.escapeShellArg (if probe.applicableWhen == null then "" else probe.applicableWhen))
    ]
    + "\n";

  probeCalls = lib.concatStrings (map renderProbeCall probes);
in
pkgs.writeShellApplication {
  name = "health-check";
  runtimeInputs = with pkgs; [ coreutils ];
  excludeShellChecks = [ "SC2016" ];
  text = ''
    modeJson=0
    modeSummary=0
    catFilter=""
    probeTimeoutSeconds="''${HEALTH_CHECK_PROBE_TIMEOUT_SECONDS:-10}"

    while [ $# -gt 0 ]; do
      case "$1" in
        --json) modeJson=1; shift;;
        --summary) modeSummary=1; shift;;
        --category) catFilter="$2"; shift 2;;
        --category=*) catFilter="''${1#--category=}"; shift;;
        -h|--help)
          cat <<USAGE
    Usage: health-check [--json|--summary] [--category=<cat[,cat...]>]

    Categories: bin, app, config, daemon, secret, auth, nix, misc
    Statuses: pass, fail, skip. A probe skips when its applicability command
    reports the thing is not meant to be running right now, so a component that
    is dormant by design never counts as a failure.
    Every probe is bounded at ''${probeTimeoutSeconds}s, and exceeding that counts as a failure.
    Exit code: 0 when no applicable probe fails, 1 when any fails.
    USAGE
          exit 0;;
        *) printf 'unknown arg: %s\n' "$1" >&2; exit 2;;
      esac
    done

    passCount=0
    failCount=0
    skipCount=0
    jsonRecords=""

    jsonEscape() {
      printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
    }

    runProbe() {
      local probeCategory="$1"
      local probeName="$2"
      local probeBody="$3"
      local probeApplicability="''${4:-}"

      if [ -n "$catFilter" ]; then
        if ! printf ',%s,' "$catFilter" | grep -qF ",$probeCategory,"; then
          return
        fi
      fi

      local status probeReason applicabilityExit bodyExit
      probeReason=""
      applicabilityExit=0
      bodyExit=0

      if [ -n "$probeApplicability" ]; then
        probeReason="$(timeout "$probeTimeoutSeconds" bash -c "$probeApplicability" 2>/dev/null)" ||
          applicabilityExit=$?
      fi

      if [ "$applicabilityExit" = 124 ]; then
        status=fail
        failCount=$((failCount + 1))
        probeReason="applicability check timed out after ''${probeTimeoutSeconds}s"
      elif [ "$applicabilityExit" != 0 ]; then
        status=skip
        skipCount=$((skipCount + 1))
        if [ -z "$probeReason" ]; then
          probeReason="not applicable"
        fi
      else
        probeReason=""
        timeout "$probeTimeoutSeconds" bash -c "$probeBody" >/dev/null 2>&1 || bodyExit=$?
        if [ "$bodyExit" = 0 ]; then
          status=pass
          passCount=$((passCount + 1))
        else
          status=fail
          failCount=$((failCount + 1))
          if [ "$bodyExit" = 124 ]; then
            probeReason="timed out after ''${probeTimeoutSeconds}s"
          fi
        fi
      fi

      if [ "$modeJson" = 1 ]; then
        local record
        record="{\"category\":\"$(jsonEscape "$probeCategory")\",\"name\":\"$(jsonEscape "$probeName")\",\"status\":\"$status\""
        if [ -n "$probeReason" ]; then
          record="$record,\"reason\":\"$(jsonEscape "$probeReason")\""
        fi
        record="$record}"
        if [ -z "$jsonRecords" ]; then
          jsonRecords="$record"
        else
          jsonRecords="$jsonRecords,$record"
        fi
      elif [ "$modeSummary" = 0 ]; then
        local color symbol detail
        detail=""
        if [ -n "$probeReason" ]; then
          detail=" ($probeReason)"
        fi
        if [ "$status" = pass ]; then
          color=32; symbol="✓"
        elif [ "$status" = skip ]; then
          color=90; symbol="-"
        else
          color=31; symbol="✗"
        fi
        printf "  \033[%sm%s\033[0m [%-6s] %s%s\n" "$color" "$symbol" "$probeCategory" "$probeName" "$detail"
      fi
    }

    ${probeCalls}

    if [ "$modeJson" = 1 ]; then
      printf '[%s]\n' "$jsonRecords"
    elif [ "$modeSummary" = 1 ]; then
      printf 'health-check: %d pass, %d fail, %d skip\n' "$passCount" "$failCount" "$skipCount"
    else
      total=$((passCount + failCount))
      if [ "$skipCount" -gt 0 ]; then
        printf '\n%d/%d passed (%d failed, %d skipped)\n' "$passCount" "$total" "$failCount" "$skipCount"
      else
        printf '\n%d/%d passed (%d failed)\n' "$passCount" "$total" "$failCount"
      fi
    fi

    if [ "$failCount" -gt 0 ]; then
      exit 1
    fi
    exit 0
  '';
}
