{ pkgs, username, home-version, ... }:
{
	home.username = username;
	home.homeDirectory = "/home/${username}";
	home.stateVersion = home-version;
	programs.home-manager.enable = true;
	news.display = "silent";

	imports = [
		./modules/pipx.nix
		./modules/dooit.nix
		./modules/sdkman.nix
	];

	home.packages = with pkgs; [
		insomnia
		uv
	];
}
