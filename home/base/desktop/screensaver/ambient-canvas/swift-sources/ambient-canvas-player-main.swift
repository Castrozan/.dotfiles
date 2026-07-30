import AppKit

@main
struct AmbientCanvasPlayerEntryPoint {
    static func main() {
        guard CommandLine.arguments.count > 2 else {
            FileHandle.standardError.write(
                Data(
                    "ambient-canvas-player: expected a segment manifest file path and a playback dwell override file path\n"
                        .utf8
                )
            )
            exit(1)
        }

        let recordedSegmentManifestFileUrl = URL(fileURLWithPath: CommandLine.arguments[1])
        let playbackDwellOverrideFileUrl = URL(fileURLWithPath: CommandLine.arguments[2])

        let ambientCanvasPlayerApplication = NSApplication.shared
        ambientCanvasPlayerApplication.setActivationPolicy(.regular)

        let ambientCanvasPlayerWindowController = AmbientCanvasPlayerWindowController(
            recordedSegmentManifestFileUrl: recordedSegmentManifestFileUrl,
            playbackDwellOverrideFileUrl: playbackDwellOverrideFileUrl
        )
        ambientCanvasPlayerWindowController.presentPinnedScreensaverWindow()

        ambientCanvasPlayerApplication.run()
    }
}
