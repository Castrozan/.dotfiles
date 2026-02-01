{ lib, ... }:
{
  options.openclaw.workspace = lib.mkOption {
    type = lib.types.str;
    default = "openclaw";
    description = "Workspace directory name relative to home";
  };
}
