runHook preInstall

mkdir -p "$out/share/herdr/plugins/annotate/bin" "$out/share/herdr/plugins/annotate/scripts" "$out/bin"
cp herdr-plugin.toml "$out/share/herdr/plugins/annotate/"
cp scripts/plannotator-tui.sh "$out/share/herdr/plugins/annotate/scripts/"
install -m755 "$annotationRuntime" "$out/share/herdr/plugins/annotate/bin/herdr-annotate.exe"
install -m755 "$reviewRuntime" "$out/share/herdr/plugins/annotate/bin/plannotator-tui.exe"
wrapProgram "$out/share/herdr/plugins/annotate/bin/herdr-annotate.exe" --prefix PATH : "$runtimePath"
wrapProgram "$out/share/herdr/plugins/annotate/bin/plannotator-tui.exe" --prefix PATH : "$runtimePath"
ln -s "$out/share/herdr/plugins/annotate/bin/herdr-annotate.exe" "$out/bin/herdr-annotate"
ln -s "$out/share/herdr/plugins/annotate/bin/plannotator-tui.exe" "$out/bin/plannotator-tui"

runHook postInstall
