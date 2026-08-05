runHook preInstall
mkdir -p "$out"
cp "$mainJs" "$out/main.js"
cp "$manifestJson" "$out/manifest.json"
if [ -n "${stylesCss:-}" ]; then
	cp "$stylesCss" "$out/styles.css"
fi
runHook postInstall
