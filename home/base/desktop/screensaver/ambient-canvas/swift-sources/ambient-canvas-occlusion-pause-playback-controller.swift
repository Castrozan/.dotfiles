import AppKit

final class AmbientCanvasOcclusionPausePlaybackController {
    private let observedWindow: NSWindow
    private let recordedLoopVideoView: AmbientCanvasRecordedLoopVideoView

    init(observedWindow: NSWindow, recordedLoopVideoView: AmbientCanvasRecordedLoopVideoView) {
        self.observedWindow = observedWindow
        self.recordedLoopVideoView = recordedLoopVideoView
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(synchronizePlaybackWithWindowVisibility),
            name: NSWindow.didChangeOcclusionStateNotification,
            object: observedWindow
        )
    }

    @objc private func synchronizePlaybackWithWindowVisibility() {
        if observedWindow.occlusionState.contains(.visible) {
            recordedLoopVideoView.resumePlayback()
        } else {
            recordedLoopVideoView.pausePlayback()
        }
    }
}
