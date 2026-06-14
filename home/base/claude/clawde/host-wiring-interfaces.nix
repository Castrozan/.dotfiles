{ config, lib, ... }:
{
  options.clawde = {
    machinesRegistry = lib.mkOption {
      type = lib.types.attrsOf lib.types.anything;
      default = { };
      description = "Fleet machine registry keyed by host alias (per-host platform and the fields agent declarations read, such as tailscaleIp and username), injected by the consuming configuration. Replaces the in-tree private-config/machines.nix read so the module is relocatable into its own repository.";
    };

    dotfilesRepoPath = lib.mkOption {
      type = lib.types.str;
      default = "${config.home.homeDirectory}/.dotfiles";
      description = "Absolute path to the dotfiles checkout this fleet member tracks, advertised in fleet.json. Injected by the consuming configuration; defaults to ~/.dotfiles.";
    };

    stewardLiveCheckoutPayloadPath = lib.mkOption {
      type = lib.types.nullOr lib.types.str;
      default = null;
      description = "Absolute path to a live editable steward payload checkout to symlink as the steward skill, enabling the steward to self-edit its payload. Null symlinks the immutable in-store payload instead (no self-edit). Injected by the consuming configuration.";
    };

    claudePackage = lib.mkOption {
      type = lib.types.nullOr lib.types.package;
      default = null;
      description = "The claude-code package whose executable agents launch via lib.getExe. Injected by the consuming configuration; the clawde module does not pin claude-code itself.";
    };
  };
}
