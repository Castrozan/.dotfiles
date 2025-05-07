{
	description = "Nix e Home Manager configuration for my Ubuntu company laptop";

	inputs = {
		nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    	home-manager = {
      		url = "github:nix-community/home-manager";
      		inputs.nixpkgs.follows = "nixpkgs";
    	};
  	};

  	outputs = { self, nixpkgs, home-manager, ... }:
	let
		system = "x86_64-linux";
		username = "lucas.zanoni";
		home-version = "23.11";
		pkgs = import nixpkgs {
			inherit system;
			config.allowUnfree = true;
		};
	in {
		homeConfigurations = {
			"${username}@${system}" = home-manager.lib.homeManagerConfiguration {
				inherit pkgs;

				extraSpecialArgs = {
					inherit username home-version;
				};

				modules = [ ./home.nix ];
			};
		};
	};
}
