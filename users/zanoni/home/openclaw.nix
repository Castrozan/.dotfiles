{
  openclaw = {
    memorySync = {
      enable = true;
      remoteHost = "workpc";
      remoteUser = "lucas.zanoni";
      agents = [ "jarvis" ];
    };

    userName = "Lucas";
    gatewayPort = 18789;
    gatewayService.enable = true;
    notifyTopic = "cleber-lucas-2f2ea57a";
    defaults.model = {
      primary = "anthropic/claude-opus-4-6";
      heartbeat = "anthropic/claude-opus-4-6";
      subagents = "anthropic/claude-opus-4-6";
    };
    agents = {
      clever = {
        enable = true;
        isDefault = true;
        emoji = "🤖";
        role = "home/personal — NixOS, home automation, overnight work";
        model.primary = "anthropic/claude-opus-4-6";
        workspace = "openclaw";
        tts.voice = "en-US-JennyNeural";
        telegram.enable = true;
        discord.enable = true;
        skills = [
          "avatar"
          "bash"
          "bot-bridge"
          "browser"
          "claude-code-oneshot"
          "commit"
          "context7"
          "dotfiles-expert"
          "hey-clever"
          "hn"
          "model-switch"
          "nix-expert"
          "openclaw-doctor"
          "pdf"
          "pull"
          "rebuild"
          "repomix"
          "sourcebot"
          "summarize"
          "system-health"
          "talk-to-user"
          "test"
          "tmux"
          "worktrees"
          "yahoo-finance"
        ];
      };
      golden = {
        enable = true;
        emoji = "🌟";
        role = "research & discovery — deep dives, analysis, long-form thinking";
        model.primary = "nvidia/moonshotai/kimi-k2.5";
        workspace = "openclaw/golden";
        tts.voice = "en-US-AriaNeural";
        telegram.enable = true;
        discord.enable = true;
      };
      jarvis = {
        enable = true;
        emoji = "🔵";
        role = "J.A.R.V.I.S. — Just A Rather Very Intelligent System. Personal AI butler in the style of Tony Stark's JARVIS. British wit, impeccable manners, anticipates needs before spoken. Addresses Lucas as 'sir'. Manages all systems with understated competence.";
        model.primary = "anthropic/claude-opus-4-6";
        workspace = "openclaw/jarvis";
        tts.voice = "en-GB-RyanNeural";
        telegram.enable = true;
        discord.enable = true;
        telegram.botName = "Jarvis";
      };
    };
  };
}
