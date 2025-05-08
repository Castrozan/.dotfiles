{ pkgs, username, home-version, ... }:
{
	home.username = username;
	home.homeDirectory = "/home/${username}";
	home.stateVersion = home-version;
	programs.home-manager.enable = true;

	imports = [
		./modules/pipx.nix
		./modules/dooit.nix
	];

	home.packages = with pkgs; [
		insomnia
	];
}
