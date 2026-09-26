{
  helpers,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;

  maccyConfiguration = helpers.homeManagerTestConfigurationForDarwin [ ../maccy-home-manager.nix ];
  launchConfiguration = maccyConfiguration.launchd.agents.maccy.config;
  expectedArguments = [
    "/Applications/Maccy.app/Contents/MacOS/Maccy"
    "-KeyboardShortcuts_popup"
    ''"{\"carbonKeyCode\":9,\"carbonModifiers\":768}"''
    "-pasteByDefault"
    "<true/>"
    "-SUEnableAutomaticChecks"
    "<false/>"
    "-loginItemEnabled"
    "<false/>"
  ];
  activationCommands = lib.concatMapStringsSep "\n" (entry: entry.data) (
    builtins.attrValues maccyConfiguration.home.activation
  );
in
{
  domain-desktop-maccy-preferences-use-native-launch-arguments =
    mkEvalCheck "domain-desktop-maccy-preferences-use-native-launch-arguments"
      (launchConfiguration.ProgramArguments == expectedArguments)
      "Maccy must receive its shortcut string and typed Boolean preferences through its native UserDefaults argument domain";

  domain-desktop-maccy-activation-does-not-access-protected-preferences =
    mkEvalCheck "domain-desktop-maccy-activation-does-not-access-protected-preferences"
      (!(lib.hasInfix "org.p0deje.Maccy" activationCommands))
      "Rebuild activation must not access Maccy's protected preferences from the terminal, which triggers AppData permission requests";
}
