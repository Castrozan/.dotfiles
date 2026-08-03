{
  claude-code = {
    imports = [
      ../home/base/agents
      ../home/base/claude
    ];
  };
  clawde = {
    imports = [
      ../home/base/agents
      ../home/base/clawde
    ];
  };
  codex = {
    imports = [
      ../home/base/agents
      ../home/base/codex
    ];
  };
  opencode = {
    imports = [
      ../home/base/agents
      ../home/base/opencode
    ];
  };
  pi = ../home/base/pi;
  default = {
    imports = [
      ../home/base/claude
      ../home/base/clawde
      ../home/base/codex
      ../home/base/opencode
      ../home/base/agents
      ../home/base/pi
    ];
  };
}
