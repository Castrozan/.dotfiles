{
  helpers,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  configuration = helpers.homeManagerTestConfiguration [ ../google-workspace-cli-home-manager.nix ];
  packageNames = map (
    package: package.name or package.pname or "unknown"
  ) configuration.home.packages;
  hasPackageMatching = pattern: builtins.any (name: builtins.match pattern name != null) packageNames;
in
{
  domain-dev-google-workspace-cli-package =
    mkEvalCheck "domain-dev-google-workspace-cli-package"
      (hasPackageMatching ".*google-workspace-cli-auth-login-with-chrome-global.*")
      "google workspace cli auth helper should be installed";

  domain-dev-google-chat-browser-cli-package =
    mkEvalCheck "domain-dev-google-chat-browser-cli-package"
      (hasPackageMatching ".*google-chat-browser-cli.*")
      "google chat browser cli should be installed as the non-GCP fallback";

  domain-dev-google-cloud-sdk-package =
    mkEvalCheck "domain-dev-google-cloud-sdk-package" (hasPackageMatching ".*google-cloud-sdk.*")
      "google cloud sdk should be installed for google workspace cli setup";
}
