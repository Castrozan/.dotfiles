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
		# ./modules/m2.nix
	];

	home.packages = with pkgs; [
		git
		xclip
		curl
		zip
		unzip
		gnutar
		curl
		lazydocker

		insomnia
		uv
		postman
		redisinsight
		lens
	];
}
