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
  rootlessGithubConfiguration = helpers.homeManagerTestConfiguration [
    ../github-rootless-home-manager.nix
    { systemd.user.enable = false; }
  ];
  rootlessGithubServiceFiles = builtins.filter (name: lib.hasPrefix ".config/systemd/user/" name) (
    builtins.attrNames rootlessGithubConfiguration.home.file
  );
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
  domain-dev-rootless-github-loads-only-approved-secret =
    mkEvalCheck "domain-dev-rootless-github-loads-only-approved-secret"
      (
        builtins.attrNames rootlessGithubConfiguration.age.secrets == [ "credentials/github-com-token" ]
        && rootlessGithubConfiguration.age.secrets."credentials/github-com-token".mode == "0400"
        && rootlessGithubConfiguration.age.identityPaths == [ "/home/test/.config/age/keys.txt" ]
      )
      "Rootless GitHub auth must load only the shared GitHub credential through the cloud-local identity";

  domain-dev-rootless-github-mounts-before-auth-without-services =
    mkEvalCheck "domain-dev-rootless-github-mounts-before-auth-without-services"
      (
        rootlessGithubServiceFiles == [ ]
        && builtins.elem "setupGithubAuthentication" rootlessGithubConfiguration.home.activation.mountDotGithubCredential.before
        && builtins.elem "setupGithubAuthentication" rootlessGithubConfiguration.home.activation.setupDotGithubHttps.after
      )
      "Rootless activation must mount the credential before native login and configure HTTPS after login without services";

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
