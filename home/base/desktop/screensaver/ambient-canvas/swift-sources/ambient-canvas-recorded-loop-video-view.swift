import AVFoundation
import AppKit

final class AmbientCanvasRecordedLoopVideoView: NSView {
    private let recordedLoopQueuePlayer = AVQueuePlayer()
    private let recordedLoopPlayerLayer = AVPlayerLayer()
    private var recordedLoopPlayerLooper: AVPlayerLooper?
    private var shuffledSegmentPlayback: AmbientCanvasShuffledSegmentPlayback?

    private let playbackDwellOverrideFileUrl: URL

    init(recordedSegmentManifestFileUrl: URL, playbackDwellOverrideFileUrl: URL) {
        self.playbackDwellOverrideFileUrl = playbackDwellOverrideFileUrl
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

        recordedLoopQueuePlayer.isMuted = true
        startPlayback(of: recordedSegmentManifestFileUrl)
    }

    required init?(coder: NSCoder) {
        fatalError("AmbientCanvasRecordedLoopVideoView does not support NSCoder initialization")
    }

    private func startPlayback(of recordedSegmentManifestFileUrl: URL) {
        guard
            let recordedSegmentManifest = AmbientCanvasRecordedSegmentManifest.load(
                fromManifestFileUrl: recordedSegmentManifestFileUrl
            )
        else {
            return
        }
        let segmentFileUrls = recordedSegmentManifest.segmentFileUrls(
            relativeTo: recordedSegmentManifestFileUrl
        )
        guard segmentFileUrls.count > 1 else {
            recordedLoopPlayerLooper = AVPlayerLooper(
                player: recordedLoopQueuePlayer,
                templateItem: AVPlayerItem(url: segmentFileUrls[0])
            )
            recordedLoopQueuePlayer.play()
            return
        }
        let segmentPlayback = AmbientCanvasShuffledSegmentPlayback(
            player: recordedLoopQueuePlayer,
            segments: recordedSegmentManifest.segments,
            segmentFileUrls: segmentFileUrls,
            playbackDwellOverrideFileUrl: playbackDwellOverrideFileUrl
        )
        shuffledSegmentPlayback = segmentPlayback
        segmentPlayback.startFirstSegment()
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
