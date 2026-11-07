{ pkgs, inputs, ... }:
let
  copyThroughTerminalClipboardEscape = ''printf "\033]52;c;%s\a" "$(printf %s {{text}} | ${pkgs.coreutils}/bin/base64 -w 0)" > /dev/tty'';
  readSystemClipboard =
    if pkgs.stdenv.hostPlatform.isDarwin then
      "pbpaste"
    else
      "${pkgs.wl-clipboard}/bin/wl-paste --no-newline";
  deltaPagerWithEditorLinks = "delta --paging=never --detect-dark-light always --hyperlinks --hyperlinks-file-link-format=\"lazygit-edit://{path}:{line}\"";
  review-changes = pkgs.writeShellScriptBin "review-changes" ''
    exec ${pkgs.python312}/bin/python3 ${./scripts/review_changes}/review_changes_cli.py "$@"
  '';
in
{
  home.packages = [ review-changes ];

  programs.lazygit = {
    enable = true;
    package = inputs.lazygit.packages.${pkgs.stdenv.hostPlatform.system}.default;

    settings = {
      os = {
        shell = "${pkgs.bashInteractive}/bin/bash -c";
        copyToClipboardCmd = copyThroughTerminalClipboardEscape;
        readFromClipboardCmd = readSystemClipboard;
      };
      gui.showDivergenceFromBaseBranch = "arrowAndNumber";
      git.pagers = [
        { pager = deltaPagerWithEditorLinks; }
        { pager = "${deltaPagerWithEditorLinks} --side-by-side"; }
      ];
    };
  };
}
