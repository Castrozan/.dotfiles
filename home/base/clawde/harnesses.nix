{ config, lib, ... }:
{
  clawde.harnesses =
    lib.optionalAttrs (config ? claude) {
      claude.package = config.claude.package;
    }
    // lib.optionalAttrs (config ? codex) {
      codex.package = config.codex.unwrappedPackage;
    };
}
