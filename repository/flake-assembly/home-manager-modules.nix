{
  claude-code = {
    imports = [
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../home/base/claude
    ];
  };
  clawde = {
    imports = [
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../home/base/clawde
    ];
  };
  codex = {
    imports = [
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../home/base/codex
    ];
  };
  opencode = {
    imports = [
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../home/base/opencode
    ];
  };
  pi = ../../home/base/pi;
  default = {
    imports = [
      ../../home/base/claude
      ../../home/base/clawde
      ../../home/base/codex
      ../../home/base/opencode
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../home/base/pi
    ];
  };
}
