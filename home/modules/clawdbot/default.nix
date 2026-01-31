# OpenClaw (formerly Clawdbot/Moltbot) - Personal AI assistant
# https://github.com/openclaw/openclaw
# https://openclaw.ai
{ ... }:
{
  imports = [
    ./install.nix
    ./config.nix
    ./channels.nix
    ./workspace.nix
    ./activation.nix
  ];
}
