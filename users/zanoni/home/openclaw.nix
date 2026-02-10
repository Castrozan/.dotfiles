{
  openclaw = {
    userName = "Lucas";
    gatewayPort = 18789;
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
      };
    };
  };
}
