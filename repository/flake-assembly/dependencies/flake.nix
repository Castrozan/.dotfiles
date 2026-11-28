{
  outputs = _: { };

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-26.05";
    nixpkgs-unstable.url = "github:nixos/nixpkgs/nixos-unstable";
    nixpkgs-latest.url = "github:nixos/nixpkgs/nixos-unstable";
    home-manager.url = "github:nix-community/home-manager/release-26.05";
    home-manager.inputs.nixpkgs.follows = "nixpkgs";

    nix-darwin.url = "github:nix-darwin/nix-darwin/nix-darwin-26.05";
    nix-darwin.inputs.nixpkgs.follows = "nixpkgs";

    stylix.url = "github:danth/stylix/release-26.05";
    stylix.inputs.nixpkgs.follows = "nixpkgs";

    private-config = {
      url = "git+ssh://git@github.com/Castrozan/private-config";
      flake = false;
    };

    arr-stack = {
      url = "git+ssh://git@github.com/Castrozan/arr-stack";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };

    commit-provenance = {
      url = "git+ssh://git@github.com/Castrozan/commit-provenance?rev=0d7a6e0d35b922571597cbaa9d9b718ae040f3cb";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };

    hammerspoon = {
      url = "git+ssh://git@github.com/Castrozan/hammerspoon-config?ref=main&rev=8fd88976e812f34fe0a56b074b1e767d13fffb4b";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };

    home-assistant.url = "git+ssh://git@github.com/Castrozan/home-assistant?rev=43f3b0003b76e2cbafeb8ed2d64a19c200da5ed7";
    home-assistant.inputs.nixpkgs.follows = "nixpkgs";

    clawde.url = "github:Castrozan/clawde/d707cf1441140c49a3cd2d62387d51297dcfd9e8";
    clawde.inputs.nixpkgs.follows = "nixpkgs";

    avatar = {
      url = "github:Castrozan/avatar/214c18269f12906c34a6644b3479b9501dd3f97a";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        home-manager.follows = "home-manager";
        nix-darwin.follows = "nix-darwin";
      };
    };

    agent-evals.url = "github:Castrozan/agent-evals/dc8600fc5f8ec9adc16c5f39af5e15176bb630f5";
    agent-evals.inputs.nixpkgs.follows = "nixpkgs";

    read-it-later = {
      url = "git+ssh://git@github.com/Castrozan/read-it-later?rev=0df55c61667ae42b26a19f985b5e73346c9dfcf0";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    neovim = {
      url = "git+ssh://git@github.com/Castrozan/neovim?rev=1a2b6491bde018afdff52cf31e878d44c791b670";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };

    orchestrator.url = "git+ssh://git@github.com/Castrozan/orchestrator?rev=377cf0edb12f707ed52d87042664275ccc6c9ef7";
    orchestrator.inputs.nixpkgs.follows = "nixpkgs";

    hermes.url = "github:NousResearch/hermes-agent/8fc0374447313e276f6b9a2764bfc750190c966a";

    systemd-manager-tui.url = "github:matheus-git/systemd-manager-tui";
    systemd-manager-tui.inputs.nixpkgs.follows = "nixpkgs";
    devenv.url = "github:cachix/devenv/v2.2.1";
    bluetui.url = "github:castrozan/bluetui/v0.9.1";
    hyprland.url = "github:hyprwm/Hyprland/v0.55.2";
    herdr.url = "github:Castrozan/herdr/8a1d2dd9a31f9c6382602e0b22d3e326ac570738";
    herdr-pace.url = "github:Castrozan/herdr-pace/ebc5f13ab98a589edff867e75a9cb9181131d1f0";
    herdr-pace.inputs.nixpkgs.follows = "nixpkgs";
    rex.url = "https://pkgs.superlogical.com/rex/nix/preview.tar.gz";
    rex.inputs.nixpkgs.follows = "nixpkgs";

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
    impasto.url = "github:Castrozan/impasto/3573712b436fbdff2361062d85da5f29269e73f5";
    impasto.inputs.nixpkgs.follows = "nixpkgs-unstable";
    viu.url = "github:viu-media/viu";
    viu.inputs.nixpkgs.follows = "nixpkgs";

    nixgl.url = "github:nix-community/nixGL";
    nixgl.inputs.nixpkgs.follows = "nixpkgs";
    agenix.url = "github:ryantm/agenix";
    agenix.inputs.nixpkgs.follows = "nixpkgs";

    hex = {
      url = "github:anomalyco/hex";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.home-manager.follows = "home-manager";
    };

    voxtype.url = "github:peteonrails/voxtype";
    whisp-away.url = "github:madjinn/whisp-away";
    google-workspace-cli.url = "github:googleworkspace/cli/a3768d0e82ad83cca2da97724e46bea4ff0e6dbd";

    usage-reporting = {
      url = "github:Castrozan/usage-reporting/5beb8ea582737ade306cc2c6af4856d74293b34b";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };
}
