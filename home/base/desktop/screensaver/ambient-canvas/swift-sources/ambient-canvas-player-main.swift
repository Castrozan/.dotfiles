import AppKit

@main
struct AmbientCanvasPlayerEntryPoint {
    static func main() {
        guard CommandLine.arguments.count > 1 else {
            FileHandle.standardError.write(
                Data("ambient-canvas-player: missing segment manifest file path argument\n".utf8)
            )
            exit(1)
        }

        let recordedSegmentManifestFileUrl = URL(fileURLWithPath: CommandLine.arguments[1])

        let ambientCanvasPlayerApplication = NSApplication.shared
        ambientCanvasPlayerApplication.setActivationPolicy(.regular)

        let ambientCanvasPlayerWindowController = AmbientCanvasPlayerWindowController(
            recordedSegmentManifestFileUrl: recordedSegmentManifestFileUrl
        )
        ambientCanvasPlayerWindowController.presentPinnedScreensaverWindow()

        ambientCanvasPlayerApplication.run()
    }
}
