{ ... }:
{
  claude.discordChannel.agents = {
    robson = {
      botTokenSecretName = "discord-bot-token-robson";
      role = "work — Betha, code, productivity";
      model = "opus";
    };
    jenny = {
      botTokenSecretName = "discord-bot-token-jenny";
      role = "full-stack personal agent — coding, monitoring, automation, scheduling";
      model = "sonnet";
    };
    monster = {
      botTokenSecretName = "discord-bot-token-monster";
      role = "creative assistant, brainstorming, fun tasks";
      model = "sonnet";
    };
    silver = {
      botTokenSecretName = "discord-bot-token-silver";
      role = "research and analysis — technical deep dives, documentation, investigation";
      model = "sonnet";
    };
  };
}
