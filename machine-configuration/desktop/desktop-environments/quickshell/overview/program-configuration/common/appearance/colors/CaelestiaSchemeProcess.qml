import Quickshell.Io

Process {
    id: caelestiaSchemeProcess

    signal paletteRead(var palette, string mode)
    signal paletteUnavailable
    command: ["sh", "-lc", "caelestia scheme get 2>/dev/null || true"]
    stdout: StdioCollector {
        id: caelestiaCollector
        onStreamFinished: {
            const text = caelestiaCollector.text;
            if (!text || !text.trim()) {
                caelestiaSchemeProcess.paletteUnavailable();
                return;
            }

            const ansiPattern = /\x1b\[[0-9;]*m/g;
            const lines = text.split("\n");
            let mode = "";
            const palette = ({});

            for (const rawLine of lines) {
                const line = rawLine.replace(ansiPattern, "").trim();

                if (line.startsWith("Mode:")) {
                    mode = line.split(":")[1]?.trim()?.toLowerCase() ?? "";
                    continue;
                }

                const match = line.match(/^([A-Za-z0-9_]+):\s*.*?([0-9a-fA-F]{6})$/);
                if (!match)
                    continue;

                palette[match[1]] = `#${match[2]}`;
            }

            caelestiaSchemeProcess.paletteRead(palette, mode);
        }
    }
}
