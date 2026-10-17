{
  config,
  lib,
  pkgs,
  ...
}:
let
  imageViewPlugin = pkgs.fetchFromGitHub {
    owner = "jarrodwatts";
    repo = "claude-image-view";
    rev = "370b8e7bc0708bebe9762e63534f7ca18bc3e802";
    hash = "sha256-cH2yGtD5k/zmOCE5WK8s9DoFicUnrCdzqfmp/GGoJW4=";
  };
in
{
  home.file.".local/share/claude-image-view".source = imageViewPlugin;

  home.activation.installClaudeImageView =
    lib.hm.dag.entryAfter [ "installProductionClaudePlugin" ]
      ''
        CLAUDE_CONFIG_DIR="${config.home.homeDirectory}/.claude" \
          ${config.claude.unwrappedPackage}/bin/claude plugin marketplace add ${imageViewPlugin}
        CLAUDE_CONFIG_DIR="${config.home.homeDirectory}/.claude" \
          ${config.claude.unwrappedPackage}/bin/claude plugin install image-view@claude-image-view
      '';
}
