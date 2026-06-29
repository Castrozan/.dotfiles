{
  lib,
  isDarwin,
  usesLocalStack,
  bringUpScriptBin,
  environmentPath,
}:
{
  config = lib.mkIf (isDarwin && usesLocalStack) {
    launchd.agents.mem0-openmemory-autostart = {
      enable = true;
      config = {
        Label = "com.dotfiles.mem0-openmemory-autostart";
        ProgramArguments = [
          "/bin/sh"
          "-c"
          "curl -fsS -o /dev/null --max-time 5 http://localhost:8765/docs || exec ${bringUpScriptBin}/bin/mem0-openmemory-up"
        ];
        EnvironmentVariables = {
          PATH = environmentPath;
        };
        RunAtLoad = true;
        StartInterval = 300;
        StandardOutPath = "/tmp/mem0-openmemory-autostart.log";
        StandardErrorPath = "/tmp/mem0-openmemory-autostart.log";
      };
    };
  };
}
