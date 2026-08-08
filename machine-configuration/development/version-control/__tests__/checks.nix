{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  configuration = helpers.homeManagerTestConfiguration [ ../lazygit-home-manager.nix ];
  gitCoreSettings =
    (helpers.homeManagerTestConfiguration [ ../git-home-manager.nix ]).programs.git.settings.core;
in
{
  domain-dev-lazygit-enabled =
    mkEvalCheck "domain-dev-lazygit-enabled" configuration.programs.lazygit.enable
      "lazygit should be enabled";

  domain-dev-git-editor-is-the-terminal-gated-launcher =
    mkEvalCheck "domain-dev-git-editor-is-the-terminal-gated-launcher"
      (lib.hasSuffix "git-message-editor" gitCoreSettings.editor)
      "core.editor should be the launcher gated on an attached terminal, never a bare GUI editor";
}
