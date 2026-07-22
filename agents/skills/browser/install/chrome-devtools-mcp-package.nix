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
    ./chrome-devtools-mcp-patches/lazy-devtools-universe.patch
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
    description = "Pinned chrome-devtools-mcp, self-bundled with zero npm dependencies, carrying three upstream-bug patches that together keep tool latency flat and the connection alive against the slow single-client consent-attached Chrome no matter how many tabs the user keeps open. The first makes the per-page title fetch in the page listing non-blocking and cached so an op no longer stalls a second per open tab (the listing returns instantly with cached titles that refresh in the background). The second makes the per-page DevTools universe (a CDP session plus Debugger and Network domain enablement) lazy and initialized on demand only for the one page a devtools-flavored tool actually touches, instead of eagerly built for every open tab inside the page snapshot that list_pages, new_page, take_snapshot, click and navigate all run, so those hot-path ops stop paying an O(open-tabs) burst of serialized CDP work through the consent proxy that pushed op latency past Chrome's connection-teardown threshold. The third clears the cached browser on a mid-session CDP disconnect and guards uncaughtException so a dropped connection degrades to one failed tool call and reconnects instead of killing the server and vanishing the tool namespace for the rest of the session";
    homepage = "https://github.com/ChromeDevTools/chrome-devtools-mcp";
  };
}
