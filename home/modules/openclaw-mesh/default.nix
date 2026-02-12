{
  lib,
  pkgs,
  config,
  inputs,
  ...
}:
let
  cfg = config.openclaw.mesh;

  rgbType = lib.types.listOf lib.types.ints.u8;

  gridAgentModule = lib.types.submodule {
    options = {
      id = lib.mkOption {
        type = lib.types.str;
      };
      emoji = lib.mkOption {
        type = lib.types.str;
      };
      model = lib.mkOption {
        type = lib.types.str;
      };
    };
  };

  meshConfig = {
    grid = map (a: {
      inherit (a) id emoji model;
    }) cfg.gridAgents;

    connections = {
      sshHost = cfg.connections.sshHost;
      sshUser = cfg.connections.sshUser;
      connectTimeoutSecs = cfg.connections.connectTimeoutSecs;
    };

    colors = {
      inherit (cfg.colors)
        local
        grid
        edgeActive
        edgeInactive
        inactiveNode
        nameActive
        nameInactive
        modelActive
        modelInactive
        tokens
        border
        title
        ;
    };

    motion = {
      inherit (cfg.motion)
        cameraAngleSpeed
        cameraPitchSpeed
        cameraDistance
        pulseSpeed
        pulseDecay
        depthFadeStrength
        edgeFadeStrength
        ;
    };

    timing = {
      inherit (cfg.timing)
        pollIntervalSecs
        tickRateMs
        activeThresholdMinutes
        ;
    };
  };
in
{
  options.openclaw.mesh = {
    gridAgents = lib.mkOption {
      type = lib.types.listOf gridAgentModule;
      default = [ ];
    };

    connections = {
      sshHost = lib.mkOption {
        type = lib.types.nullOr lib.types.str;
        default = null;
      };
      sshUser = lib.mkOption {
        type = lib.types.nullOr lib.types.str;
        default = null;
      };
      connectTimeoutSecs = lib.mkOption {
        type = lib.types.int;
        default = 2;
      };
    };

    colors = {
      local = lib.mkOption {
        type = rgbType;
        default = [
          50
          255
          50
        ];
      };
      grid = lib.mkOption {
        type = rgbType;
        default = [
          50
          200
          255
        ];
      };
      edgeActive = lib.mkOption {
        type = rgbType;
        default = [
          0
          255
          255
        ];
      };
      edgeInactive = lib.mkOption {
        type = rgbType;
        default = [
          0
          220
          240
        ];
      };
      inactiveNode = lib.mkOption {
        type = rgbType;
        default = [
          40
          60
          40
        ];
      };
      nameActive = lib.mkOption {
        type = rgbType;
        default = [
          100
          255
          100
        ];
      };
      nameInactive = lib.mkOption {
        type = rgbType;
        default = [
          0
          150
          0
        ];
      };
      modelActive = lib.mkOption {
        type = rgbType;
        default = [
          255
          255
          100
        ];
      };
      modelInactive = lib.mkOption {
        type = rgbType;
        default = [
          150
          150
          50
        ];
      };
      tokens = lib.mkOption {
        type = rgbType;
        default = [
          150
          220
          255
        ];
      };
      border = lib.mkOption {
        type = rgbType;
        default = [
          0
          100
          0
        ];
      };
      title = lib.mkOption {
        type = rgbType;
        default = [
          50
          255
          50
        ];
      };
    };

    motion = {
      cameraAngleSpeed = lib.mkOption {
        type = lib.types.float;
        default = 0.04;
      };
      cameraPitchSpeed = lib.mkOption {
        type = lib.types.float;
        default = 0.012;
      };
      cameraDistance = lib.mkOption {
        type = lib.types.float;
        default = 8.0;
      };
      pulseSpeed = lib.mkOption {
        type = lib.types.float;
        default = 0.15;
      };
      pulseDecay = lib.mkOption {
        type = lib.types.float;
        default = 0.95;
      };
      depthFadeStrength = lib.mkOption {
        type = lib.types.float;
        default = 0.75;
      };
      edgeFadeStrength = lib.mkOption {
        type = lib.types.float;
        default = 0.85;
      };
    };

    timing = {
      pollIntervalSecs = lib.mkOption {
        type = lib.types.int;
        default = 5;
      };
      tickRateMs = lib.mkOption {
        type = lib.types.int;
        default = 33;
      };
      activeThresholdMinutes = lib.mkOption {
        type = lib.types.int;
        default = 5;
      };
    };
  };

  config = {
    home.packages = [
      inputs.openclaw-mesh.packages.${pkgs.stdenv.hostPlatform.system}.default
    ];

    xdg.configFile."openclaw-mesh/config.json".text = builtins.toJSON meshConfig;
  };
}
