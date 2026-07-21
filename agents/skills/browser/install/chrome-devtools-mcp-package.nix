{
  pkgs,
  nodejs,
}:
let
  version = "1.6.0";
  npmTarball = pkgs.fetchurl {
    url = "https://registry.npmjs.org/chrome-devtools-mcp/-/chrome-devtools-mcp-${version}.tgz";
    hash = "sha256-HmMsLZcUtPgrTPq077nOV1CFx1/+XpdyODEprwEsnIQ=";
  };
in
pkgs.stdenv.mkDerivation {
  pname = "chrome-devtools-mcp";
  inherit version;
  src = npmTarball;

  patches = [
    ./chrome-devtools-mcp-patches/nonblocking-page-titles.patch
    ./chrome-devtools-mcp-patches/survive-cdp-disconnect.patch
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  dontConfigure = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall

    bundleRoot="$out/lib/chrome-devtools-mcp"
    mkdir -p "$bundleRoot"
    cp -R . "$bundleRoot/"

    makeWrapper ${nodejs}/bin/node "$out/bin/chrome-devtools-mcp" \
      --add-flags "$bundleRoot/build/src/bin/chrome-devtools-mcp.js"

    runHook postInstall
  '';

  meta = {
    description = "Pinned chrome-devtools-mcp, self-bundled with zero npm dependencies, carrying two upstream-bug patches: one makes the per-page title fetch in the page listing non-blocking and cached so an op no longer stalls a second per open tab against the slow consent-attached Chrome (the listing returns instantly with cached titles that refresh in the background, keeping op latency flat regardless of how many tabs the user keeps open), the other clears the cached browser on a mid-session CDP disconnect and guards uncaughtException so a dropped connection degrades to one failed tool call and reconnects instead of killing the server and vanishing the tool namespace for the rest of the session";
    homepage = "https://github.com/ChromeDevTools/chrome-devtools-mcp";
  };
}
