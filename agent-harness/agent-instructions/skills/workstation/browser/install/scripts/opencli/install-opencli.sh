#!/usr/bin/env bash
runHook preInstall
: "${out:?}"
mkdir -p "$out/lib/opencli"
cp -R node_modules "$out/lib/opencli/"
packageRoot="$out/lib/opencli/node_modules/@jackwener/opencli"
substituteInPlace "$packageRoot/dist/src/daemon.js" \
	--replace-fail "return !origin || origin.startsWith('chrome-extension://');" \
	"return origin?.startsWith('chrome-extension://') === true && Boolean(process.env.OPENCLI_BRIDGE_TOKEN) && new URL(req.url, 'http://127.0.0.1').searchParams.get('token') === process.env.OPENCLI_BRIDGE_TOKEN;" \
	--replace-fail 'daemonVersion: PKG_VERSION,' \
	'daemonVersion: PKG_VERSION, managedJobId: process.env.OPENCLI_JOB_IDENTIFIER,' \
	--replace-fail "if (!req.headers['x-opencli']) {" \
	"if (!req.headers['x-opencli'] || (!(req.method === 'GET' && pathname === '/status') && (!process.env.OPENCLI_BRIDGE_TOKEN || req.headers.authorization !== 'Bearer ' + process.env.OPENCLI_BRIDGE_TOKEN))) {"
substituteInPlace "$packageRoot/dist/src/browser/daemon-transport.js" \
	--replace-fail "const OPENCLI_HEADERS = { 'X-OpenCLI': '1' };" \
	"const OPENCLI_HEADERS = { 'X-OpenCLI': '1', Authorization: 'Bearer ' + (process.env.OPENCLI_BRIDGE_TOKEN ?? '') };"
substituteInPlace "$packageRoot/dist/src/browser/daemon-lifecycle.js" \
	--replace-fail 'const launch = resolveDaemonLaunchSpec();' \
	'throw new Error("Managed browser jobs must run inside opencli-run; daemon autostart is disabled."); const launch = resolveDaemonLaunchSpec();'
substituteInPlace "$packageRoot/dist/src/main.js" \
	--replace-fail 'registerUpdateNoticeOnExit();' "" \
	--replace-fail 'checkForUpdateBackground();' ""
makeWrapper "$OPENCLI_NODE" "$out/bin/opencli" \
	--add-flags "$packageRoot/dist/src/main.js"
runHook postInstall
