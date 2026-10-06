forge:
let
  forgeHosts = {
    github = "github.com";
    gitlab = "gitlab.com";
  };
  repositories = [
    {
      github = ".dotfiles";
      gitlab = "dotfiles";
    }
    {
      github = "dotfiles-private";
      gitlab = "dotfiles-private";
    }
    {
      github = "zanoni-system";
      gitlab = "zanoni-system";
    }
  ];
  repositoryPath =
    provider: repository: "${forgeHosts.${provider}}:Castrozan/${repository.${provider}}.git";
  repositoryAliases =
    repository:
    builtins.concatLists (
      builtins.map (provider: [
        "git@${repositoryPath provider repository}"
        "https://${forgeHosts.${provider}}/Castrozan/${repository.${provider}}.git"
      ]) (builtins.attrNames forgeHosts)
    );
  repositoryRule =
    repository:
    let
      targetUrl = "git@${repositoryPath forge repository}";
    in
    {
      name = targetUrl;
      value.insteadOf = builtins.filter (alias: alias != targetUrl) (repositoryAliases repository);
    };
in
builtins.listToAttrs (builtins.map repositoryRule repositories)
