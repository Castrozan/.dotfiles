import AppKit

@main
struct AmbientCanvasPlayerEntryPoint {
    static func main() {
        guard CommandLine.arguments.count > 1 else {
            FileHandle.standardError.write(
                Data("ambient-canvas-player: missing recorded loop file path argument\n".utf8)
            )
            exit(1)
        }

        let recordedLoopFileUrl = URL(fileURLWithPath: CommandLine.arguments[1])

        let ambientCanvasPlayerApplication = NSApplication.shared
        ambientCanvasPlayerApplication.setActivationPolicy(.accessory)

        let ambientCanvasPlayerWindowController = AmbientCanvasPlayerWindowController(
            recordedLoopFileUrl: recordedLoopFileUrl
        )
        ambientCanvasPlayerWindowController.presentPinnedScreensaverWindow()

        ambientCanvasPlayerApplication.run()
    }
}
