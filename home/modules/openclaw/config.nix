{
  lib,
  ...
}:
{
  options.openclaw.workspacePath = lib.mkOption {
    type = lib.types.str;
    default = "openclaw";
    description = "Workspace directory path relative to home";
  };
}
