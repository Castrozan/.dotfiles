import AVFoundation

final class AmbientCanvasShuffledSegmentPlayback {
    private static let seekTimescale: CMTimeScale = 600

    private let player: AVQueuePlayer
    private let segments: [AmbientCanvasRecordedLoopSegment]
    private let recordedLoopFileUrl: URL
    private let segmentOrder: AmbientCanvasShuffledSegmentOrder
    private var segmentEndObserver: Any?
    private var issuedSeekGeneration = 0
    private var isPlaybackSuspended = false

    init(
        player: AVQueuePlayer,
        segments: [AmbientCanvasRecordedLoopSegment],
        recordedLoopFileUrl: URL
    ) {
        self.player = player
        self.segments = segments
        self.recordedLoopFileUrl = recordedLoopFileUrl
        self.segmentOrder = AmbientCanvasShuffledSegmentOrder(segmentCount: segments.count)
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(advancePastPlaybackEnd),
            name: .AVPlayerItemDidPlayToEndTime,
            object: nil
        )
    }

    deinit {
        removeSegmentEndObserver()
        NotificationCenter.default.removeObserver(self)
    }

    func startFirstSegment() {
        playNextSegment()
    }

    func suspendPlayback() {
        isPlaybackSuspended = true
        player.pause()
    }

    func resumePlayback() {
        isPlaybackSuspended = false
        player.play()
    }

    @objc private func advancePastPlaybackEnd(_ notification: Notification) {
        guard
            let endedItem = notification.object as? AVPlayerItem,
            endedItem === player.currentItem
        else {
            return
        }
        playNextSegment()
    }

    private func playNextSegment() {
        let segment = segments[segmentOrder.nextSegmentIndex()]
        removeSegmentEndObserver()
        issuedSeekGeneration += 1
        let seekGeneration = issuedSeekGeneration
        player.seek(
            to: CMTime(seconds: segment.startSeconds, preferredTimescale: Self.seekTimescale),
            toleranceBefore: .zero,
            toleranceAfter: .zero
        ) { [weak self] seekFinished in
            guard let self, seekFinished, seekGeneration == self.issuedSeekGeneration else {
                return
            }
            self.observeEnd(of: segment)
            if !self.isPlaybackSuspended {
                self.player.play()
            }
        }
    }

    private func observeEnd(of segment: AmbientCanvasRecordedLoopSegment) {
        removeSegmentEndObserver()
        let dwellSeconds = AmbientCanvasPlaybackDwellOverride.effectiveDwellSeconds(
            recordedDwellSeconds: segment.durationSeconds,
            besideRecordedLoop: recordedLoopFileUrl
        )
        let endTime = CMTime(
            seconds: segment.startSeconds + dwellSeconds,
            preferredTimescale: Self.seekTimescale
        )
        segmentEndObserver = player.addBoundaryTimeObserver(
            forTimes: [NSValue(time: endTime)],
            queue: .main
        ) { [weak self] in
            self?.playNextSegment()
        }
    }

    private func removeSegmentEndObserver() {
        guard let existingObserver = segmentEndObserver else {
            return
        }
        player.removeTimeObserver(existingObserver)
        segmentEndObserver = nil
    }
}
