import AVFoundation
import AppKit

final class AmbientCanvasRecordedLoopVideoView: NSView {
    private let recordedLoopQueuePlayer = AVQueuePlayer()
    private let recordedLoopPlayerLayer = AVPlayerLayer()
    private var recordedLoopPlayerLooper: AVPlayerLooper?
    private var shuffledSegmentPlayback: AmbientCanvasShuffledSegmentPlayback?
    private var pendingPresentationRelease: DispatchWorkItem?
    private var isPlaybackPaused = false

    private let playbackDwellOverrideFileUrl: URL

    init(recordedSegmentManifestFileUrl: URL, playbackDwellOverrideFileUrl: URL) {
        self.playbackDwellOverrideFileUrl = playbackDwellOverrideFileUrl
        super.init(frame: .zero)
        wantsLayer = true
        let backingLayer = CALayer()
        backingLayer.backgroundColor =
            AmbientCanvasPlayerWindowController
            .deepNavyBackgroundColor.cgColor
        layer = backingLayer

        recordedLoopPlayerLayer.player = recordedLoopQueuePlayer
        recordedLoopPlayerLayer.videoGravity = .resizeAspect
        recordedLoopPlayerLayer.backgroundColor =
            AmbientCanvasPlayerWindowController
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
        guard !isPlaybackPaused else {
            return
        }
        isPlaybackPaused = true
        let presentationRelease = DispatchWorkItem { [weak self] in
            guard let self, self.isPlaybackPaused else {
                return
            }
            self.recordedLoopPlayerLayer.player = nil
            self.pendingPresentationRelease = nil
        }
        pendingPresentationRelease = presentationRelease
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5, execute: presentationRelease)
        guard let shuffledSegmentPlayback else {
            recordedLoopQueuePlayer.pause()
            return
        }
        shuffledSegmentPlayback.suspendPlayback()
    }

    func resumePlayback() {
        guard isPlaybackPaused else {
            return
        }
        isPlaybackPaused = false
        pendingPresentationRelease?.cancel()
        pendingPresentationRelease = nil
        if recordedLoopPlayerLayer.player == nil {
            recordedLoopPlayerLayer.player = recordedLoopQueuePlayer
        }
        guard let shuffledSegmentPlayback else {
            recordedLoopQueuePlayer.play()
            return
        }
        shuffledSegmentPlayback.resumePlayback()
    }
}
