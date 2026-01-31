# OpenClaw (formerly Clawdbot/Moltbot) - Personal AI assistant
# https://github.com/openclaw/openclaw
# https://openclaw.ai
#
# Config strategy: Nix manages only workspace identity files and package install.
# Runtime config (openclaw.json) is managed locally by openclaw itself.
{ ... }:
{
  imports = [
    ./install.nix
    ./workspace.nix
  ];
}
