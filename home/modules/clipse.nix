{ pkgs, config, ... }:
let
  # Custom fork of clipse
  clipse-zanoni = pkgs.buildGoModule {
    pname = "clipse";
    version = "zanoni.v1.2.1";

    src = pkgs.fetchFromGitHub {
      owner = "castrozan";
      repo = "clipse";
      rev = "cbc20e7deba13bbf188e32280cc9e51f25970b53";
      sha256 = "sha256-NpKw5HtighOF+7Ym9Q973uoLtmYQrBmvSPwyGIKi19M=";
    };

    vendorHash = "sha256-LxwST4Zjxq6Fwc47VeOdv19J3g/DHZ7Fywp2ZvVR06I=";
    proxyVendor = true;

    buildInputs = with pkgs; [
      xorg.libX11
      xorg.libXtst
    ];
    nativeBuildInputs = with pkgs; [ pkg-config ];

    tags = [ "wayland" ];

    meta = with pkgs.lib; {
      description = "Clipboard manager for Wayland (custom fork)";
      homepage = "https://github.com/castrozan/clipse";
      license = licenses.mit;
    };
  };
in
{
  home.packages = [
    pkgs.wl-clipboard
    clipse-zanoni
  ];

  xdg.configFile."clipse/config.json".text = builtins.toJSON {
    historyFile = "clipboard_history.json";
    maxHistory = 100;
    allowDuplicates = false;
    themeFile = "${config.home.homeDirectory}/.config/hypr-theme/current/theme/clipse.json";
    tempDir = "tmp_files";
    logFile = "clipse.log";
    keyBindings = {
      choose = "enter";
      clearSelected = "S";
      down = "down";
      end = "end";
      filter = "/";
      home = "home";
      more = "?";
      nextPage = "right";
      prevPage = "left";
      preview = "t";
      quit = "q";
      remove = "x";
      selectDown = "ctrl+down";
      selectSingle = "s";
      selectUp = "ctrl+up";
      togglePin = "p";
      togglePinned = "tab";
      up = "up";
      yankFilter = "ctrl+s";
    };
    imageDisplay = {
      type = "kitty";
      scaleX = 9;
      scaleY = 9;
      heightCut = 2;
    };
  };

  systemd.user.services.clipse = {
    Unit = {
      Description = "Clipse clipboard manager listener";
      After = [ "graphical-session.target" ];
      StartLimitIntervalSec = 30;
      StartLimitBurst = 3;
    };
    Service = {
      Type = "simple";
      ExecStart = "${clipse-zanoni}/bin/clipse --listen-shell";
      Restart = "always";
      RestartSec = 5;
    };
    Install.WantedBy = [ "graphical-session.target" ];
  };
}
