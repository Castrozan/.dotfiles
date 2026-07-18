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
            contentRect: hammerspoonManagedInitialWindowFrame(),
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

    private func hammerspoonManagedInitialWindowFrame() -> NSRect {
        let initialWidth: CGFloat = 1280
        let initialHeight: CGFloat = 800
        guard let visibleScreenFrame = NSScreen.main?.visibleFrame else {
            return NSRect(x: 0, y: 0, width: initialWidth, height: initialHeight)
        }
        let centeredOriginX =
            visibleScreenFrame.origin.x + (visibleScreenFrame.width - initialWidth) / 2
        let centeredOriginY =
            visibleScreenFrame.origin.y + (visibleScreenFrame.height - initialHeight) / 2
        return NSRect(
            x: centeredOriginX, y: centeredOriginY, width: initialWidth, height: initialHeight
        )
    }
}
