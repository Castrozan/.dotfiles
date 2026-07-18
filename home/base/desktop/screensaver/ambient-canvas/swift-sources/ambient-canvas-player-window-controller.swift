import AppKit

final class AmbientCanvasPlayerWindowController {
    static let pinnedScreensaverWindowTitle = "ambient-canvas-gpu-screensaver"
    static let deepNavyBackgroundColor = NSColor(
        red: 0x0a / 255.0,
        green: 0x1a / 255.0,
        blue: 0x2f / 255.0,
        alpha: 1.0
    )

    private let recordedLoopFileUrl: URL
    private var screensaverWindow: NSWindow?
    private var recordedLoopVideoView: AmbientCanvasRecordedLoopVideoView?
    private var visibilityGatedPlaybackController: AmbientCanvasVisibilityGatedPlaybackController?

    init(recordedLoopFileUrl: URL) {
        self.recordedLoopFileUrl = recordedLoopFileUrl
    }

    func presentPinnedScreensaverWindow() {
        let hostingWindow = NSWindow(
            contentRect: fullScreenWindowFrame(),
            styleMask: [.titled, .fullSizeContentView, .resizable],
            backing: .buffered,
            defer: false
        )
        hostingWindow.title = Self.pinnedScreensaverWindowTitle
        hostingWindow.titleVisibility = .hidden
        hostingWindow.titlebarAppearsTransparent = true
        hostingWindow.isMovable = false
        hostingWindow.hasShadow = false
        hostingWindow.backgroundColor = Self.deepNavyBackgroundColor
        hostingWindow.standardWindowButton(.closeButton)?.isHidden = true
        hostingWindow.standardWindowButton(.miniaturizeButton)?.isHidden = true
        hostingWindow.standardWindowButton(.zoomButton)?.isHidden = true

        let videoView = AmbientCanvasRecordedLoopVideoView(recordedLoopFileUrl: recordedLoopFileUrl)
        hostingWindow.contentView = videoView
        hostingWindow.orderFrontRegardless()

        visibilityGatedPlaybackController = AmbientCanvasVisibilityGatedPlaybackController(
            observedWindow: hostingWindow,
            recordedLoopVideoView: videoView
        )
        screensaverWindow = hostingWindow
        recordedLoopVideoView = videoView
    }

    private func fullScreenWindowFrame() -> NSRect {
        return NSScreen.main?.frame ?? NSRect(x: 0, y: 0, width: 1440, height: 900)
    }
}
