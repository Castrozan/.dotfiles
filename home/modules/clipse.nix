{ pkgs, ... }:
let
  # Wrapper script that opens clipse TUI and restarts listener after
  clipse-tui = pkgs.writeShellScriptBin "clipse-tui" ''
    # -fc $PPID forces terminal to close after selection
    ${pkgs.clipse}/bin/clipse -fc $PPID
    # Restart the listener after TUI closes (TUI kills it)
    systemctl --user restart clipse.service &
  '';
in
{
  home.packages = with pkgs; [
    wl-clipboard
    clipse-tui
  ];

  # Configure clipse as a systemd user service to run in the background
  systemd.user.services.clipse = {
    Unit = {
      Description = "Clipse clipboard manager";
      After = [ "graphical-session.target" ];
      PartOf = [ "graphical-session.target" ];
    };

    Service = {
      Type = "simple";
      ExecStart = "${pkgs.clipse}/bin/clipse --listen-shell";
      Restart = "on-failure";
      RestartSec = "5s";
    };

    Install = {
      WantedBy = [ "graphical-session.target" ];
    };
  };

  systemd.user.startServices = "sd-switch";
}
