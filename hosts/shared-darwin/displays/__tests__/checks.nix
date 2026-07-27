{
  pkgs,
  lib,
  ...
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit pkgs lib;
    inputs = null;
    nixpkgs-version = null;
    home-version = null;
  };
  inherit (helpers) mkEvalCheck;

  displaysConfig = import ../default.nix {
    inherit lib pkgs;
    username = "testuser";
  };

  postActivationLines = lib.splitString "\n" displaysConfig.system.activationScripts.postActivation.text.content;

  directoryServiceLines = lib.filter (line: lib.hasInfix "/usr/bin/dscl " line) postActivationLines;

  timeoutExportLines = lib.filter (
    line: lib.hasInfix "export TIMEOUT_BINARY_PATH=" line
  ) postActivationLines;

  everyDirectoryServiceReadIsTimeBounded =
    directoryServiceLines != [ ]
    && lib.all (line: lib.hasInfix "\"$TIMEOUT_BINARY_PATH\" " line) directoryServiceLines;

  theTimeoutBinaryResolvesToARealExecutable =
    timeoutExportLines != [ ] && lib.all (line: lib.hasInfix "/bin/timeout" line) timeoutExportLines;

  noDirectoryServiceReadSwallowsItsOwnFailure = lib.all (
    line: !lib.hasInfix "|| true" line
  ) directoryServiceLines;
in
{
  macbook-displays-directory-service-reads-are-time-bounded =
    mkEvalCheck "macbook-displays-directory-service-reads-are-time-bounded"
      everyDirectoryServiceReadIsTimeBounded
      "Every `dscl` read in the display-configuration postActivation must run under the timeout binary, because dscl is a synchronous client of opendirectoryd and this script is inlined directly into the root activation under `set -e` and `set -o pipefail`, so a wedged directory service blocks the whole switch forever instead of failing, leaving the new home generation linked while /run/current-system stays on the old one";

  macbook-displays-timeout-binary-resolves-to-a-real-executable =
    mkEvalCheck "macbook-displays-timeout-binary-resolves-to-a-real-executable"
      theTimeoutBinaryResolvesToARealExecutable
      "TIMEOUT_BINARY_PATH must be exported as a concrete path to a timeout executable, because the bound on the `dscl` read is applied by expanding that variable; were it exported empty or unset the expansion would run the wrong program and the read would fail into an empty UUID rather than being bounded";

  macbook-displays-directory-service-reads-must-not-swallow-their-own-failure =
    mkEvalCheck "macbook-displays-directory-service-reads-must-not-swallow-their-own-failure"
      noDirectoryServiceReadSwallowsItsOwnFailure
      "No `dscl` read here may end in `|| true`, because the UUID it returns is interpolated into the CoreBrightness preference key `CBUser-<uuid>`; swallowing a failure would write a malformed key against a live system preference file and report a green activation, so a bounded failure must still abort the switch loudly";
}
