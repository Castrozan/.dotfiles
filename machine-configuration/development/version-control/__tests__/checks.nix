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
  personalRepositoryRouting = import ../personal-repository-routing.nix;
  routesEveryRepository =
    forge: expectedTargets:
    let
      routing = personalRepositoryRouting forge;
    in
    builtins.attrNames routing == expectedTargets
    && lib.all (
      target:
      builtins.length routing.${target}.insteadOf == 3
      && !(builtins.elem target routing.${target}.insteadOf)
    ) expectedTargets;
in
{
  domain-dev-lazygit-enabled =
    mkEvalCheck "domain-dev-lazygit-enabled" configuration.programs.lazygit.enable
      "lazygit should be enabled";

  domain-dev-git-editor-is-the-terminal-gated-launcher =
    mkEvalCheck "domain-dev-git-editor-is-the-terminal-gated-launcher"
      (lib.hasSuffix "git-message-editor" gitCoreSettings.editor)
      "core.editor should be the launcher gated on an attached terminal, never a bare GUI editor";

  domain-dev-personal-repositories-select-github =
    mkEvalCheck "domain-dev-personal-repositories-select-github"
      (routesEveryRepository "github" [
        "git@github.com:Castrozan/.dotfiles.git"
        "git@github.com:Castrozan/dotfiles-private.git"
        "git@github.com:Castrozan/zanoni-system.git"
      ])
      "GitHub selection routes every personal repository's other SSH and HTTPS aliases to GitHub";

  domain-dev-personal-repositories-select-gitlab =
    mkEvalCheck "domain-dev-personal-repositories-select-gitlab"
      (routesEveryRepository "gitlab" [
        "git@gitlab.com:Castrozan/dotfiles-private.git"
        "git@gitlab.com:Castrozan/dotfiles.git"
        "git@gitlab.com:Castrozan/zanoni-system.git"
      ])
      "GitLab selection routes every personal repository's other SSH and HTTPS aliases to GitLab";
}
