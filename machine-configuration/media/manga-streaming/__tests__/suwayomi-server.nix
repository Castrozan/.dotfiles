{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  suwayomiModule = import ../suwayomi-server-home-manager.nix {
    config = {
      home.homeDirectory = "/home/zanoni";
    };
    inherit lib;
    latest = {
      suwayomi-server = "/nix/store/test-suwayomi-server";
    };
  };

  suwayomiUnit = suwayomiModule.systemd.user.services.suwayomi-server;
  environmentEntries = suwayomiUnit.Service.Environment;
  environmentText = lib.concatStringsSep " " environmentEntries;
  forcedSettingPrefix = "-Dsuwayomi.tachidesk.config.server.";

  unitStartsWithTheUserSession = suwayomiUnit.Install.WantedBy == [ "default.target" ];

  downloadsAreArchivedAsCbz = lib.hasInfix "${forcedSettingPrefix}downloadAsCbz=true" environmentText;

  downloadsLandInTheKavitaLibraryRoot = lib.hasInfix "${forcedSettingPrefix}downloadsPath=/home/zanoni/arr-stack/data/manga" environmentText;

  javaToolOptionsSurviveSystemdWordSplitting = builtins.any (
    entry: lib.hasPrefix ''"JAVA_TOOL_OPTIONS='' entry && lib.hasSuffix ''"'' entry
  ) environmentEntries;

  bindAddressIsForcedAndNotAWildcard =
    lib.hasInfix "${forcedSettingPrefix}ip=" environmentText
    && !(lib.hasInfix "${forcedSettingPrefix}ip=0.0.0.0" environmentText);

  unitRefusesToRunWithoutTheDataDrive =
    suwayomiUnit.Unit.ConditionPathIsMountPoint == "/home/zanoni/arr-stack/data";

  restartRetriesAreNeverRateLimited = suwayomiUnit.Unit.StartLimitIntervalSec == 0;
in
{
  chise-suwayomi-starts-with-the-user-session =
    mkEvalCheck "chise-suwayomi-starts-with-the-user-session" unitStartsWithTheUserSession
      "Suwayomi is the acquisition half of the manga stack, so its unit must be wanted by default.target; left out, the unit deploys but never runs and Kavita reads an empty library forever";

  chise-suwayomi-downloads-as-cbz =
    mkEvalCheck "chise-suwayomi-downloads-as-cbz" downloadsAreArchivedAsCbz
      "downloads must be forced to CBZ, because Kavita ingests archives and silently skips the loose per-chapter image folders Suwayomi writes by default";

  chise-suwayomi-downloads-into-the-kavita-library-root =
    mkEvalCheck "chise-suwayomi-downloads-into-the-kavita-library-root"
      downloadsLandInTheKavitaLibraryRoot
      "the download root must be the arr data drive's manga tree that Kavita bind-mounts, not the Tachidesk data directory in the home partition, or manga lands where no reader serves it and the disk guard never watches it grow";

  chise-suwayomi-java-tool-options-quoted-as-one-assignment =
    mkEvalCheck "chise-suwayomi-java-tool-options-quoted-as-one-assignment"
      javaToolOptionsSurviveSystemdWordSplitting
      "the JAVA_TOOL_OPTIONS entry must stay wrapped in double quotes: systemd splits an unquoted Environment= line on whitespace, so dropping them turns every forced setting after the first into a malformed assignment and Suwayomi quietly falls back to whatever server.conf happens to hold";

  chise-suwayomi-never-binds-the-wildcard-interface =
    mkEvalCheck "chise-suwayomi-never-binds-the-wildcard-interface" bindAddressIsForcedAndNotAWildcard
      "Suwayomi ships no login, so its bind address must be forced to the tailnet address rather than left at the 0.0.0.0 default; the host firewall is the only other thing keeping a loginless manga server off every interface";

  chise-suwayomi-refuses-to-run-without-the-data-drive =
    mkEvalCheck "chise-suwayomi-refuses-to-run-without-the-data-drive"
      unitRefusesToRunWithoutTheDataDrive
      "the unit must condition on the arr data drive being mounted, or a disconnected drive lets Suwayomi download into the bare mountpoint on the root filesystem and the library splits across two places";

  chise-suwayomi-restart-retries-are-never-rate-limited =
    mkEvalCheck "chise-suwayomi-restart-retries-are-never-rate-limited"
      restartRetriesAreNeverRateLimited
      "the start rate limiter must stay off: the forced tailnet bind fails until tailscaled has the interface up, and systemd's default burst gives up before that on a cold boot";
}
