{ pkgs, ... }:
{
  packages = [ pkgs.coreutils ];

  scripts.project-lint.exec = ''
    exec ${pkgs.coreutils}/bin/timeout --kill-after=10s 10m node ./node_modules/eslint/bin/eslint.js "$@"
  '';
  scripts.project-test.exec = ''
    exec ${pkgs.coreutils}/bin/timeout --kill-after=10s 5m npm test -- --runInBand "$@"
  '';
  scripts.project-build.exec = ''
    exec ${pkgs.coreutils}/bin/timeout --kill-after=10s 15m env NODE_OPTIONS=--openssl-legacy-provider npm run build "$@"
  '';

  processes.front-counter = {
    exec = ''
      env NODE_OPTIONS=--openssl-legacy-provider node ./node_modules/webpack-dev-server/bin/webpack-dev-server.js --mode development --open=false --config configs/webpack.dev.js --env fc --host "''${DEVENV_CONTAINER_BIND_ADDRESS:-127.0.0.1}" --port 8080
    '';
    restart.on = "never";
    ready = {
      http.get.port = 8080;
      period = 2;
      timeout = 300;
    };
  };
}
