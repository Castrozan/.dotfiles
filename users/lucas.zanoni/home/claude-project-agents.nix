{ config, ... }:
let
  inherit (config.home) homeDirectory;
in
{
  claude.projectAgents.agents = {
    ai-first-initiative = {
      projectDirectory = "${homeDirectory}/repo/ai-first-initiative";
      model = "opus";
    };
    esfinge = {
      projectDirectory = "${homeDirectory}/repo/esfinge";
      model = "opus";
    };
    betha-pm = {
      projectDirectory = "${homeDirectory}/repo/betha-pm";
      model = "opus";
    };
  };
}
