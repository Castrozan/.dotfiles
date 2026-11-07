{ pkgs }:
pkgs.python312Packages.buildPythonApplication {
  pname = "hypruse";
  version = "0.11.0";
  pyproject = true;
  src = pkgs.fetchFromGitHub {
    owner = "IlyasKhallouki";
    repo = "hypruse";
    rev = "v0.11.0";
    hash = "sha256-MjDpzB5qDPHnPYOzxg9pa5mAzjb1SMvo67kFLq8pU2k=";
  };
  build-system = [ pkgs.python312Packages.hatchling ];
  dependencies = [ pkgs.python312Packages.mcp ];
  nativeBuildInputs = [ pkgs.makeWrapper ];
  pythonImportsCheck = [ "hypruse.verbs" ];
  postFixup = ''
    wrapProgram "$out/bin/hypruse" \
      --prefix PATH : ${
        pkgs.lib.makeBinPath [
          pkgs.hyprland
          pkgs.grim
          pkgs.wtype
          pkgs.systemd
          pkgs.imagemagick
          pkgs.wl-clipboard
        ]
      }
  '';
  doInstallCheck = true;
  installCheckPhase = ''
    "$out/bin/hypruse" --help | grep -q 'click_ui NAME'
    "$out/bin/hypruse" desktop --help >/dev/null
  '';
  meta = {
    description = "Native Hyprland desktop control through shell verbs";
    homepage = "https://github.com/IlyasKhallouki/hypruse";
    license = pkgs.lib.licenses.mit;
    platforms = pkgs.lib.platforms.linux;
    mainProgram = "hypruse";
  };
}
