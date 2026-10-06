{ pkgs, loaders }:
pkgs.runCommand "pi-loop-guard-file-entrypoint" { } ''
  cp -R ${loaders}/node_modules/@wkqco33/pi-loop-guard "$out"
  chmod u+w "$out" "$out/package.json"
  ${pkgs.jq}/bin/jq '.pi.extensions = ["./extensions/loop-guard.ts"]' \
    "$out/package.json" > "$out/package.json.tmp"
  mv "$out/package.json.tmp" "$out/package.json"
''
