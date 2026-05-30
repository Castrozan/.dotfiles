{
  config,
  lib,
  pkgs,
  ...
}:
let
  healthCheckLib = import ./lib.nix { inherit lib; };

  probeSubmodule = lib.types.submodule {
    options = {
      category = lib.mkOption {
        type = lib.types.enum [
          "bin"
          "app"
          "config"
          "daemon"
          "secret"
          "auth"
          "nix"
          "misc"
        ];
        description = "Probe category for --category filtering.";
      };
      name = lib.mkOption {
        type = lib.types.str;
        description = "Human-readable probe label.";
      };
      probe = lib.mkOption {
        type = lib.types.lines;
        description = "Bash snippet that exits 0 on success. Build via healthCheckLib helpers; do not write raw shell at the call site.";
      };
    };
  };

  renderProbeCall =
    probe:
    "runProbe ${lib.escapeShellArg probe.category} ${lib.escapeShellArg probe.name} ${lib.escapeShellArg probe.probe}\n";

  probeCalls = lib.concatStrings (map renderProbeCall config.healthCheck.probes);

  healthCheckScript = pkgs.writeShellApplication {
    name = "health-check";
    runtimeInputs = with pkgs; [ coreutils ];
    # Probes that interpolate runtime variables (e.g. $HOME inside mkAppProbe)
    # appear inside single-quoted runProbe arguments after lib.escapeShellArg.
    # They expand later inside `bash -c "$probeBody"`, not at the call site.
    excludeShellChecks = [ "SC2016" ];
    text = ''
      modeJson=0
      modeSummary=0
      catFilter=""

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
      Exit code: 0 when all probes pass, 1 when any fails.
      USAGE
            exit 0;;
          *) printf 'unknown arg: %s\n' "$1" >&2; exit 2;;
        esac
      done

      passCount=0
      failCount=0
      jsonRecords=""

      jsonEscape() {
        printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
      }

      runProbe() {
        local probeCategory="$1"
        local probeName="$2"
        local probeBody="$3"

        if [ -n "$catFilter" ]; then
          if ! printf ',%s,' "$catFilter" | grep -qF ",$probeCategory,"; then
            return
          fi
        fi

        local status
        if bash -c "$probeBody" >/dev/null 2>&1; then
          status=pass
          passCount=$((passCount + 1))
        else
          status=fail
          failCount=$((failCount + 1))
        fi

        if [ "$modeJson" = 1 ]; then
          local record
          record="{\"category\":\"$(jsonEscape "$probeCategory")\",\"name\":\"$(jsonEscape "$probeName")\",\"status\":\"$status\"}"
          if [ -z "$jsonRecords" ]; then
            jsonRecords="$record"
          else
            jsonRecords="$jsonRecords,$record"
          fi
        elif [ "$modeSummary" = 0 ]; then
          local color symbol
          if [ "$status" = pass ]; then
            color=32; symbol="✓"
          else
            color=31; symbol="✗"
          fi
          printf "  \033[%sm%s\033[0m [%-6s] %s\n" "$color" "$symbol" "$probeCategory" "$probeName"
        fi
      }

      ${probeCalls}

      if [ "$modeJson" = 1 ]; then
        printf '[%s]\n' "$jsonRecords"
      elif [ "$modeSummary" = 1 ]; then
        printf 'health-check: %d pass, %d fail\n' "$passCount" "$failCount"
      else
        total=$((passCount + failCount))
        printf '\n%d/%d passed (%d failed)\n' "$passCount" "$total" "$failCount"
      fi

      if [ "$failCount" -gt 0 ]; then
        exit 1
      fi
      exit 0
    '';
  };
in
{
  options.healthCheck.probes = lib.mkOption {
    type = lib.types.listOf probeSubmodule;
    default = [ ];
    description = "Liveness probes. Each module appends its own via healthCheckLib helpers.";
  };

  config = {
    _module.args.healthCheckLib = healthCheckLib;
    home.packages = [ healthCheckScript ];
  };
}
