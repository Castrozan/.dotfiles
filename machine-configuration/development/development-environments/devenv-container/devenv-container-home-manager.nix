{
  config,
  lib,
  pkgs,
  latest,
  isDarwin,
  ...
}:
let
  containerSources = ./scripts;
  runtimePackages = [
    pkgs.docker-compose
    pkgs.git
  ]
  ++ lib.optional isDarwin latest.colima;
  containerPolicyContents = builtins.toJSON {
    workspace_root = "${config.home.homeDirectory}/repo";
    state_root = "${config.xdg.stateHome}/devenv-container";
    image_directory = "${./container}";
    virtual_machine = isDarwin;
    virtual_machine_profile = "devenv";
    virtual_machine_cpus = 2;
    virtual_machine_memory_gib = 4;
    virtual_machine_disk_gib = 32;
    container_cpus = 2;
    container_memory_bytes = 3 * 1024 * 1024 * 1024;
    container_process_limit = 512;
    maximum_running_containers = 1;
    command_timeout_seconds = 600;
    session_timeout_seconds = 8 * 60 * 60;
    idle_timeout_seconds = 300;
  };
  containerPolicy = pkgs.writeText "devenv-container-policy.json" containerPolicyContents;
  containerCommand = pkgs.writeShellScriptBin "devenv-container" ''
    export PATH="${lib.makeBinPath runtimePackages}:$PATH"
    export PYTHONPATH="${containerSources}"
    export DEVENV_CONTAINER_POLICY="${containerPolicy}"
    exec ${pkgs.python312}/bin/python3 ${containerSources}/devenv_container.py "$@"
  '';
in
{
  home.packages = [ containerCommand ] ++ runtimePackages;
  xdg.configFile."devenv-container/policy.json".text = containerPolicyContents;

  launchd.agents.devenv-container-cleanup = lib.mkIf isDarwin {
    enable = true;
    config = {
      ProgramArguments = [
        "${containerCommand}/bin/devenv-container"
        "collect"
      ];
      StartInterval = 60;
      ProcessType = "Background";
      StandardOutPath = "${config.xdg.stateHome}/devenv-container-cleanup.log";
      StandardErrorPath = "${config.xdg.stateHome}/devenv-container-cleanup.log";
    };
  };

  systemd.user.services.devenv-container-cleanup = lib.mkIf (!isDarwin) {
    Unit.Description = "Stop unused development containers";
    Service = {
      Type = "oneshot";
      ExecStart = "${containerCommand}/bin/devenv-container collect";
      TimeoutStartSec = 60;
    };
  };
  systemd.user.timers.devenv-container-cleanup = lib.mkIf (!isDarwin) {
    Unit.Description = "Collect unused development containers";
    Timer = {
      OnBootSec = "1min";
      OnUnitActiveSec = "1min";
    };
    Install.WantedBy = [ "timers.target" ];
  };
}
