{ config, ... }:
let
  skillSetsBaseDirectory = "${config.home.homeDirectory}/.local/share/claude-skill-sets";
  personalSkillSetDirectory = "${skillSetsBaseDirectory}/personal";
  aplicacoesSkillSetDirectory = "${skillSetsBaseDirectory}/aplicacoes";
  protocoloSkillSetDirectory = "${skillSetsBaseDirectory}/protocolo";
  triageSkillSetDirectory = "${skillSetsBaseDirectory}/triage";
in
{
  claude.discordChannel.agents = {
    robson = {
      botTokenSecretName = "discord-bot-token-robson";
      role = "work — Betha, code, productivity";
      model = "opus";
      skillDirectories = [
        personalSkillSetDirectory
        aplicacoesSkillSetDirectory
      ];
    };
    jenny = {
      botTokenSecretName = "discord-bot-token-jenny";
      role = "full-stack personal agent — coding, monitoring, automation, scheduling";
      model = "sonnet";
      skillDirectories = [ personalSkillSetDirectory ];
    };
    monster = {
      botTokenSecretName = "discord-bot-token-monster";
      role = "creative assistant, brainstorming, fun tasks";
      model = "sonnet";
      skillDirectories = [ personalSkillSetDirectory ];
    };
    silver = {
      botTokenSecretName = "discord-bot-token-silver";
      role = "research and analysis — technical deep dives, documentation, investigation";
      model = "sonnet";
      skillDirectories = [ personalSkillSetDirectory ];
    };
  };
}
