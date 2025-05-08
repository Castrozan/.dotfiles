{ pkgs, username, home-version, ... }:
{
	home.username = username;
	home.homeDirectory = "/home/${username}";
	home.stateVersion = home-version;
	programs.home-manager.enable = true;

	home.packages = with pkgs; [
		insomnia
	];
}
