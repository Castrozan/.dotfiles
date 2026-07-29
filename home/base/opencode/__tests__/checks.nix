{
  pkgs,
  lib,
  inputs,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;
  deployedOpencodeSettings = builtins.fromJSON cfg.home.file.".config/opencode/opencode.json".text;
in
{
  domain-opencode-package =
    mkEvalCheck "domain-opencode-package" (hasPackageMatching ".*opencode.*")
      "opencode package should be installed";

  domain-opencode-bin-wrapper =
    mkEvalCheck "domain-opencode-bin-wrapper" (builtins.hasAttr ".local/bin/opencode" cfg.home.file)
      ".local/bin/opencode should be in home.file";

  domain-opencode-default-model = mkEvalCheck "domain-opencode-default-model" (
    deployedOpencodeSettings.model == "openai/gpt-5.6-sol"
  ) "opencode must default to GPT-5.6 Sol through the OpenAI OAuth provider";

  domain-opencode-default-model-variant = mkEvalCheck "domain-opencode-default-model-variant" (
    deployedOpencodeSettings.agent.build.model == "openai/gpt-5.6-sol"
    && deployedOpencodeSettings.agent.build.variant == "max"
  ) "opencode's default build agent must run GPT-5.6 Sol at max effort";
}
