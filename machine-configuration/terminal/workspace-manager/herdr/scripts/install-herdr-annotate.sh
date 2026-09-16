runHook preInstall

mkdir -p "$out/share/herdr-plugin/bin" "$out/share/herdr-plugin/scripts" "$out/bin"
cp herdr-plugin.toml "$out/share/herdr-plugin/"
cp scripts/plannotator-tui.sh "$out/share/herdr-plugin/scripts/"
install -m755 "$annotationRuntime" "$out/share/herdr-plugin/bin/herdr-annotate.exe"
install -m755 "$reviewRuntime" "$out/share/herdr-plugin/bin/plannotator-tui.exe"
wrapProgram "$out/share/herdr-plugin/bin/herdr-annotate.exe" --prefix PATH : "$runtimePath"
wrapProgram "$out/share/herdr-plugin/bin/plannotator-tui.exe" --prefix PATH : "$runtimePath"
ln -s "$out/share/herdr-plugin/bin/herdr-annotate.exe" "$out/bin/herdr-annotate"
ln -s "$out/share/herdr-plugin/bin/plannotator-tui.exe" "$out/bin/plannotator-tui"

runHook postInstall
