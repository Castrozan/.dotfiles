{
  lib,
  mkEvalCheck,
  chromeGlobalLauncherConfiguration,
}:
let
  versionDriftRestarterAgentIsWired =
    chromeGlobalLauncherConfiguration.launchd.agents ? "chrome-global-version-drift-restarter";

  versionDriftRestarterAgentConfiguration =
    chromeGlobalLauncherConfiguration.launchd.agents."chrome-global-version-drift-restarter".config;

  versionDriftRestarterProgramArguments = lib.concatStringsSep " " versionDriftRestarterAgentConfiguration.ProgramArguments;

  versionDriftRestarterProgramArgumentsReferenceEntrypointAndLauncher =
    lib.hasInfix "restart_chrome_global_on_version_drift.py" versionDriftRestarterProgramArguments
    && lib.hasInfix "summon-chrome-global" versionDriftRestarterProgramArguments;

  versionDriftRestarterRunsPeriodically = versionDriftRestarterAgentConfiguration.StartInterval > 0;

  versionDetectionScriptSource = builtins.readFile ../scripts/chrome_global_version_drift_restarter/chrome_version_detection.py;

  frontmostGuardScriptSource = builtins.readFile ../scripts/chrome_global_version_drift_restarter/frontmost_application.py;

  restartActionScriptSource = builtins.readFile ../scripts/chrome_global_version_drift_restarter/chrome_global_restart.py;

  entrypointScriptSource = builtins.readFile ../scripts/chrome_global_version_drift_restarter/restart_chrome_global_on_version_drift.py;

  versionDriftRestarterDetectsDriftByComparingOnDiskAndRunningVersions =
    lib.hasInfix "--version" versionDetectionScriptSource
    && lib.hasInfix "framework/Versions/" versionDetectionScriptSource;

  frontmostGuardReadsFrontmostApplicationViaListApplicationInformation = lib.hasInfix "lsappinfo" frontmostGuardScriptSource;

  versionDriftRestarterDefersRestartWhileChromeIsFrontmost =
    lib.hasInfix "chrome_is_the_frontmost_application" entrypointScriptSource
    && lib.hasInfix "deferring restart" entrypointScriptSource;

  versionDriftRestarterRelaunchKeepsChromeBareForAutoConnect =
    !lib.hasInfix "--remote-debugging-port" restartActionScriptSource;
in
{
  domain-desktop-chrome-global-version-drift-restarter-agent-wired =
    mkEvalCheck "domain-desktop-chrome-global-version-drift-restarter-agent-wired"
      versionDriftRestarterAgentIsWired
      "the chrome-global-version-drift-restarter launchd agent must be wired so a Chrome that auto-updated underneath a long-lived chrome-global session gets restarted, restoring the version match that chrome-devtools-mcp autoConnect needs";

  domain-desktop-chrome-global-version-drift-restarter-program-arguments-reference-entrypoint-and-launcher =
    mkEvalCheck
      "domain-desktop-chrome-global-version-drift-restarter-program-arguments-reference-entrypoint-and-launcher"
      versionDriftRestarterProgramArgumentsReferenceEntrypointAndLauncher
      "the agent must run the restart entrypoint and pass the summon-chrome-global launcher, proving the module evaluates under darwin pkgs and relaunches Chrome through the same bare launcher the rest of the chrome module uses";

  domain-desktop-chrome-global-version-drift-restarter-runs-periodically =
    mkEvalCheck "domain-desktop-chrome-global-version-drift-restarter-runs-periodically"
      versionDriftRestarterRunsPeriodically
      "the agent must carry a positive StartInterval so it polls for version drift on a schedule rather than only at load";

  domain-desktop-chrome-global-version-drift-restarter-detects-version-drift =
    mkEvalCheck "domain-desktop-chrome-global-version-drift-restarter-detects-version-drift"
      versionDriftRestarterDetectsDriftByComparingOnDiskAndRunningVersions
      "drift detection must read the on-disk Chrome version and the running framework version so it can tell when Chrome updated on disk while the old process kept running, the condition that breaks autoConnect";

  domain-desktop-chrome-global-version-drift-restarter-frontmost-guard-uses-lsappinfo =
    mkEvalCheck "domain-desktop-chrome-global-version-drift-restarter-frontmost-guard-uses-lsappinfo"
      frontmostGuardReadsFrontmostApplicationViaListApplicationInformation
      "the frontmost guard must read the active application via lsappinfo, the permission-free LaunchServices query, so the periodic agent never triggers a TCC automation prompt";

  domain-desktop-chrome-global-version-drift-restarter-defers-while-frontmost =
    mkEvalCheck "domain-desktop-chrome-global-version-drift-restarter-defers-while-frontmost"
      versionDriftRestarterDefersRestartWhileChromeIsFrontmost
      "the entrypoint must consult chrome_is_the_frontmost_application and take the deferring-restart branch so a detected drift never restarts Chrome while it is frontmost, interrupting active browsing";

  domain-desktop-chrome-global-version-drift-restarter-relaunch-stays-bare =
    mkEvalCheck "domain-desktop-chrome-global-version-drift-restarter-relaunch-stays-bare"
      versionDriftRestarterRelaunchKeepsChromeBareForAutoConnect
      "the restart action must not inject --remote-debugging-port; it relaunches through summon-chrome-global so Chrome stays bare for autoConnect stealth, matching the launcher invariant";
}
