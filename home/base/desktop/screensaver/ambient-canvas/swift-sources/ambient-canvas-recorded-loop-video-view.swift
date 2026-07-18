import AppKit
import AVFoundation

final class AmbientCanvasRecordedLoopVideoView: NSView {
    private let recordedLoopQueuePlayer = AVQueuePlayer()
    private let recordedLoopPlayerLayer = AVPlayerLayer()
    private var recordedLoopPlayerLooper: AVPlayerLooper?

    init(recordedLoopFileUrl: URL) {
        super.init(frame: .zero)
        wantsLayer = true
        let backingLayer = CALayer()
        backingLayer.backgroundColor = AmbientCanvasPlayerWindowController
            .deepNavyBackgroundColor.cgColor
        layer = backingLayer

        recordedLoopPlayerLayer.player = recordedLoopQueuePlayer
        recordedLoopPlayerLayer.videoGravity = .resizeAspect
        recordedLoopPlayerLayer.backgroundColor = AmbientCanvasPlayerWindowController
            .deepNavyBackgroundColor.cgColor
        backingLayer.addSublayer(recordedLoopPlayerLayer)

        recordedLoopPlayerLooper = AVPlayerLooper(
            player: recordedLoopQueuePlayer,
            templateItem: AVPlayerItem(url: recordedLoopFileUrl)
        )
        recordedLoopQueuePlayer.isMuted = true
        recordedLoopQueuePlayer.play()
    }

    required init?(coder: NSCoder) {
        fatalError("AmbientCanvasRecordedLoopVideoView does not support NSCoder initialization")
    }

    override func layout() {
        super.layout()
        recordedLoopPlayerLayer.frame = bounds
    }

    func pausePlayback() {
        recordedLoopQueuePlayer.pause()
    }

    func resumePlayback() {
        recordedLoopQueuePlayer.play()
    }
}
