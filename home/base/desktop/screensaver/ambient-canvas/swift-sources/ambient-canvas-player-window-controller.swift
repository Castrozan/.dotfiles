import AppKit

final class AmbientCanvasPlayerWindowController {
    static let pinnedScreensaverWindowTitle = "ambient-canvas-gpu-screensaver"
    static let screenCoverageFraction: CGFloat = 0.72
    static let deepNavyBackgroundColor = NSColor(
        red: 0x0a / 255.0,
        green: 0x1a / 255.0,
        blue: 0x2f / 255.0,
        alpha: 1.0
    )

    private let recordedLoopFileUrl: URL
    private var screensaverWindow: NSWindow?
    private var recordedLoopVideoView: AmbientCanvasRecordedLoopVideoView?
    private var occlusionPausePlaybackController: AmbientCanvasOcclusionPausePlaybackController?

    init(recordedLoopFileUrl: URL) {
        self.recordedLoopFileUrl = recordedLoopFileUrl
    }

    func presentPinnedScreensaverWindow() {
        let hostingWindow = NSWindow(
            contentRect: centeredScreensaverWindowFrame(),
            styleMask: [.titled, .fullSizeContentView],
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

        occlusionPausePlaybackController = AmbientCanvasOcclusionPausePlaybackController(
            observedWindow: hostingWindow,
            recordedLoopVideoView: videoView
        )
        screensaverWindow = hostingWindow
        recordedLoopVideoView = videoView
    }

    private func centeredScreensaverWindowFrame() -> NSRect {
        let screenFrame = NSScreen.main?.frame ?? NSRect(x: 0, y: 0, width: 1440, height: 900)
        let windowWidth = screenFrame.width * Self.screenCoverageFraction
        let windowHeight = screenFrame.height * Self.screenCoverageFraction
        return NSRect(
            x: screenFrame.minX + (screenFrame.width - windowWidth) / 2,
            y: screenFrame.minY + (screenFrame.height - windowHeight) / 2,
            width: windowWidth,
            height: windowHeight
        )
    }
}
