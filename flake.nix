{
  description = ''
    not A very basic flake

    Forget everything you know about nix, this is just a framework to configure apps and dotfiles.

    Outputs live in ./flake/outputs.nix to keep this file short. Inputs must
    stay here because Nix parses flake.nix statically to discover them.
  '';

  outputs = inputs: (import ./flake/outputs.nix) inputs;

  inputs = {
    # For stable packages definitions
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
    # For packages not yet in nixpkgs
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    # For latest bleeding edge packages - daily* updated with: $ nix flake update nixpkgs-latest
    nixpkgs-latest.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager/release-25.11";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

    # nix-darwin for the macbook host. Inert on Linux activations.
    nix-darwin.url = "github:nix-darwin/nix-darwin/nix-darwin-25.11";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";

    # Theming used by the macbook host (and any Linux host that opts in).
    stylix.url = "github:danth/stylix/release-25.11";
    stylix.inputs.nixpkgs.follows = "nixpkgs";

    # Private assets repo (already mounted as a git submodule at private-config/);
    # also exposed as a flake input so darwin modules that take it via inputs.
    private-config = {
      url = "git+ssh://git@github.com/Castrozan/private-config";
      flake = false;
    };

    clawde.url = "github:Castrozan/clawde";
    clawde.inputs.nixpkgs.follows = "nixpkgs";

    # Tag-pinned — keep own nixpkgs (incompatible or untested with ours)
    tui-notifier.url = "github:castrozan/tui-notifier/1.0.1";
    systemd-manager-tui.url = "github:matheus-git/systemd-manager-tui";
    systemd-manager-tui.inputs.nixpkgs.follows = "nixpkgs";
    readItNow-rc.url = "github:castrozan/readItNow-rc/1.1.0";
    devenv.url = "github:cachix/devenv/v1.11.2";
    bluetui.url = "github:castrozan/bluetui/v0.9.1";
    hyprland.url = "github:hyprwm/Hyprland/v0.55.2";

    # Own forks — follow nixpkgs (tested, no version-sensitive deps)
    cbonsai.url = "github:castrozan/cbonsai";
    cbonsai.inputs.nixpkgs.follows = "nixpkgs";
    cmatrix.url = "github:castrozan/cmatrix";
    cmatrix.inputs.nixpkgs.follows = "nixpkgs";
    tuisvn.url = "github:castrozan/tuisvn";
    tuisvn.inputs.nixpkgs.follows = "nixpkgs";
    install-nothing.url = "github:castrozan/install-nothing";
    install-nothing.inputs.nixpkgs.follows = "nixpkgs";
    lazygit.url = "github:Castrozan/lazygit";
    lazygit.inputs.nixpkgs.follows = "nixpkgs";
    viu.url = "github:viu-media/viu";
    viu.inputs.nixpkgs.follows = "nixpkgs";
    voice-pipeline.url = "github:castrozan/voice-pipeline";
    voice-pipeline.inputs.nixpkgs.follows = "nixpkgs";

    # Well-maintained, nixpkgs-agnostic
    nixgl.url = "github:nix-community/nixGL";
    nixgl.inputs.nixpkgs.follows = "nixpkgs";
    agenix.url = "github:ryantm/agenix";
    agenix.inputs.nixpkgs.follows = "nixpkgs";
    # Tracks master for nullptr guards and scene-graph fixes landed after v0.2.1.
    # See .config/quickshell/CRASHES.md for the incident log and update cadence.
    quickshell.url = "git+https://git.outfoxxed.me/quickshell/quickshell?ref=master";
    quickshell.inputs.nixpkgs.follows = "nixpkgs-unstable";

    # Third-party — keep own nixpkgs
    voxtype.url = "github:peteonrails/voxtype";
    whisp-away.url = "github:madjinn/whisp-away";
    google-workspace-cli.url = "github:googleworkspace/cli";
  };
}
