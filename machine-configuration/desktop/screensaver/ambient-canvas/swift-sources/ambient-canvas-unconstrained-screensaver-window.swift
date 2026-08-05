import AppKit

final class AmbientCanvasUnconstrainedScreensaverWindow: NSWindow {
    override func constrainFrameRect(_ proposedFrameRect: NSRect, to screen: NSScreen?) -> NSRect {
        return proposedFrameRect
    }
}
