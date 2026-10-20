{
  helpers,
  inputs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  darwinConfiguration = helpers.homeManagerTestConfigurationForDarwin [
    inputs.agenix.homeManagerModules.default
    ../temporary-directory-cleanup-home-manager.nix
  ];

  cleanupProgramArguments =
    darwinConfiguration.launchd.agents.temporary-directory-cleanup.config.ProgramArguments;

  protectedTopLevelNames = lib.pipe cleanupProgramArguments [
    (lib.imap0 (index: argument: { inherit index argument; }))
    (builtins.filter (
      entry: entry.index > 0 && builtins.elemAt cleanupProgramArguments (entry.index - 1) == "--protect"
    ))
    (map (entry: entry.argument))
  ];
in
{
  domain-system-temporary-directory-cleanup-protects-agenix =
    mkEvalCheck "domain-system-temporary-directory-cleanup-protects-agenix"
      (builtins.all (name: builtins.elem name protectedTopLevelNames) [
        "agenix"
        "agenix.d"
      ])
      "temporary directory cleanup must never age out the agenix secrets that ~/.secrets links into";
}
