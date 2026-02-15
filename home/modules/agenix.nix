{ inputs, config, ... }:
{
  imports = [ inputs.agenix.homeManagerModules.default ];

  age = {
    identityPaths = [ "${config.home.homeDirectory}/.ssh/id_ed25519" ];

    secrets.betha-credentials = {
      file = ../../secrets/betha-credentials.age;
      path = "${config.home.homeDirectory}/.secrets/betha-credentials";
    };

    secrets.skill-atendimento-env = {
      file = ../../secrets/skill-atendimento-env.age;
      path = "${config.home.homeDirectory}/.secrets/skill-atendimento-env";
    };
  };
}
