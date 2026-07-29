{ config, ... }:
{
  clawde.harnesses = {
    claude.package = config.claude.package;
    codex.package = config.codex.unwrappedPackage;
  };
}
