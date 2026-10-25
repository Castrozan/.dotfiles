{
  pkgs,
  nodejs,
  muteAudio ? false,
}:
let
  runtime = import ./opencli-package.nix { inherit pkgs nodejs; };
  extension = import ./opencli-extension.nix { inherit pkgs; };
  browser = import ./opencli-browser.nix { inherit pkgs; };
  jobBrowser =
    if muteAudio then
      pkgs.writeShellScriptBin "chromium" ''
        exec ${browser}/bin/chromium --mute-audio "$@"
      ''
    else
      browser;
  scripts = pkgs.lib.fileset.toSource {
    root = ./scripts/opencli;
    fileset = pkgs.lib.fileset.unions [
      ./scripts/opencli/opencli_job.py
      ./scripts/opencli/opencli_browser.py
      ./scripts/opencli/opencli_exec.py
      ./scripts/opencli/opencli_resources.py
      ./scripts/opencli/opencli_processes.py
      ./scripts/opencli/opencli_command.py
      ./scripts/opencli/opencli_owner.py
      ./scripts/opencli/opencli_supervisor.py
    ];
  };
  runner = pkgs.writeShellScriptBin "opencli-run" ''
    export OPENCLI_CLI=${runtime}/bin/opencli
    export OPENCLI_NODE=${nodejs}/bin/node
    export OPENCLI_DAEMON=${runtime}/lib/opencli/node_modules/@jackwener/opencli/dist/src/daemon.js
    export OPENCLI_EXTENSION=${extension}
    export OPENCLI_BROWSER=${jobBrowser}/bin/chromium
    ${pkgs.lib.optionalString pkgs.stdenv.isLinux ''
      export PATH=${pkgs.lib.makeBinPath [ pkgs.systemd ]}:"$PATH"
    ''}
    exec ${pkgs.python312}/bin/python3 ${scripts}/opencli_job.py "$@"
  '';
  command = pkgs.writeShellScriptBin "opencli" ''
    export OPENCLI_CLI=${runtime}/bin/opencli
    export OPENCLI_MANIFEST=${runtime}/lib/opencli/node_modules/@jackwener/opencli/cli-manifest.json
    export OPENCLI_JOB_RUNNER=${runner}/bin/opencli-run
    exec ${pkgs.python312}/bin/python3 ${scripts}/opencli_command.py "$@"
  '';
in
{
  packages = [
    command
    runner
  ];
  inherit command runner;
}
