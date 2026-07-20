import AppKit
import AVFoundation

final class AmbientCanvasRecordedLoopVideoView: NSView {
    private let recordedLoopQueuePlayer = AVQueuePlayer()
    private let recordedLoopPlayerLayer = AVPlayerLayer()
    private var recordedLoopPlayerLooper: AVPlayerLooper?
    private var shuffledSegmentPlayback: AmbientCanvasShuffledSegmentPlayback?

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

        let recordedLoopItem = AVPlayerItem(url: recordedLoopFileUrl)
        if let segmentTable = AmbientCanvasRecordedLoopSegmentTable
            .loadAdjacentToRecordedLoop(recordedLoopFileUrl)
        {
            recordedLoopQueuePlayer.insert(recordedLoopItem, after: nil)
            recordedLoopQueuePlayer.actionAtItemEnd = .pause
            shuffledSegmentPlayback = AmbientCanvasShuffledSegmentPlayback(
                player: recordedLoopQueuePlayer,
                segments: segmentTable.segments
            )
        } else {
            recordedLoopPlayerLooper = AVPlayerLooper(
                player: recordedLoopQueuePlayer,
                templateItem: recordedLoopItem
            )
        }
        recordedLoopQueuePlayer.isMuted = true
        shuffledSegmentPlayback?.startFirstSegment()
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
        guard let shuffledSegmentPlayback else {
            recordedLoopQueuePlayer.pause()
            return
        }
        shuffledSegmentPlayback.suspendPlayback()
    }

    func resumePlayback() {
        guard let shuffledSegmentPlayback else {
            recordedLoopQueuePlayer.play()
            return
        }
        shuffledSegmentPlayback.resumePlayback()
    }
}
