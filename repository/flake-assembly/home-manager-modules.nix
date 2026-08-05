{
  claude-code = {
    imports = [
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../agent-harness/harnesses/claude-code
    ];
  };
  clawde = {
    imports = [
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../agent-harness/harnesses/clawde
    ];
  };
  codex = {
    imports = [
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../agent-harness/harnesses/codex
    ];
  };
  opencode = {
    imports = [
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../agent-harness/harnesses/opencode
    ];
  };
  pi = ../../agent-harness/harnesses/pi;
  default = {
    imports = [
      ../../agent-harness/harnesses/claude-code
      ../../agent-harness/harnesses/clawde
      ../../agent-harness/harnesses/codex
      ../../agent-harness/harnesses/opencode
      ../../agent-harness/agent-instructions/agent-instructions-home-manager.nix
      ../../agent-harness/harnesses/pi
    ];
  };
}
