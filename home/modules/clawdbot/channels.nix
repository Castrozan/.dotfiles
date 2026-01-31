# OpenClaw channel configs — telegram, whatsapp, signal
# Note: These are part of the base config but separated for clarity.
# The actual channel values are embedded in config.nix's clawdbotBaseConfig.
# This file exists as a logical placeholder for future channel-specific options/overrides.
#
# Current channel config lives in config.nix under clawdbotBaseConfig.channels:
#   - whatsapp: dmPolicy allowlist, selfChatMode, groups requireMention
#   - telegram: enabled, tokenFile, allowFrom, streamMode partial, reactions
{ ... }:
{
  # Channel configuration is currently embedded in config.nix.
  # When channels need their own options or per-user overrides, add them here.
}
