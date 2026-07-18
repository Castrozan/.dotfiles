import AppKit

final class AmbientCanvasVisibilityGatedPlaybackController {
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
        NSWorkspace.shared.notificationCenter.addObserver(
            self,
            selector: #selector(synchronizePlaybackWithWindowVisibility),
            name: NSWorkspace.activeSpaceDidChangeNotification,
            object: nil
        )
    }

    @objc private func synchronizePlaybackWithWindowVisibility() {
        let windowIsOnScreenForTheViewer =
            observedWindow.occlusionState.contains(.visible)
            && observedWindow.isOnActiveSpace
        if windowIsOnScreenForTheViewer {
            recordedLoopVideoView.resumePlayback()
        } else {
            recordedLoopVideoView.pausePlayback()
        }
    }
}
