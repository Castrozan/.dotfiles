import AVFoundation

final class AmbientCanvasShuffledSegmentPlayback {
    private static let boundaryTimescale: CMTimeScale = 600
    private static let queuedSegmentLookahead = 2

    private let player: AVQueuePlayer
    private let segments: [AmbientCanvasRecordedSegment]
    private let segmentAssets: [AVURLAsset]
    private let segmentManifestFileUrl: URL
    private let segmentOrder: AmbientCanvasShuffledSegmentOrder
    private var segmentIndexByPlayerItem: [ObjectIdentifier: Int] = [:]
    private var currentSegmentObservation: NSKeyValueObservation?
    private var segmentDwellObserver: Any?
    private var isPlaybackSuspended = false

    init(
        player: AVQueuePlayer,
        segments: [AmbientCanvasRecordedSegment],
        segmentFileUrls: [URL],
        segmentManifestFileUrl: URL
    ) {
        self.player = player
        self.segments = segments
        self.segmentAssets = segmentFileUrls.map { AVURLAsset(url: $0) }
        self.segmentManifestFileUrl = segmentManifestFileUrl
        self.segmentOrder = AmbientCanvasShuffledSegmentOrder(segmentCount: segments.count)
        player.actionAtItemEnd = .advance
    }

    deinit {
        removeSegmentDwellObserver()
    }

    func startFirstSegment() {
        fillSegmentQueue()
        observeCurrentSegmentChanges()
        observeDwellEndOfCurrentSegment()
        player.play()
    }

    func suspendPlayback() {
        isPlaybackSuspended = true
        player.pause()
    }

    func resumePlayback() {
        isPlaybackSuspended = false
        player.play()
    }

    private func observeCurrentSegmentChanges() {
        currentSegmentObservation = player.observe(\.currentItem) { [weak self] _, _ in
            DispatchQueue.main.async {
                self?.handleCurrentSegmentChange()
            }
        }
    }

    private func handleCurrentSegmentChange() {
        forgetDequeuedPlayerItems()
        fillSegmentQueue()
        observeDwellEndOfCurrentSegment()
        if !isPlaybackSuspended {
            player.play()
        }
    }

    private func fillSegmentQueue() {
        while player.items().count < Self.queuedSegmentLookahead {
            let segmentIndex = segmentOrder.nextSegmentIndex()
            let playerItem = AVPlayerItem(asset: segmentAssets[segmentIndex])
            segmentIndexByPlayerItem[ObjectIdentifier(playerItem)] = segmentIndex
            player.insert(playerItem, after: nil)
        }
    }

    private func forgetDequeuedPlayerItems() {
        let queuedItemIdentifiers = Set(player.items().map(ObjectIdentifier.init))
        segmentIndexByPlayerItem = segmentIndexByPlayerItem.filter { playerItemEntry in
            queuedItemIdentifiers.contains(playerItemEntry.key)
        }
    }

    private func observeDwellEndOfCurrentSegment() {
        removeSegmentDwellObserver()
        guard
            let currentItem = player.currentItem,
            let currentSegmentIndex = segmentIndexByPlayerItem[ObjectIdentifier(currentItem)]
        else {
            return
        }
        let currentSegment = segments[currentSegmentIndex]
        let dwellSeconds = AmbientCanvasPlaybackDwellOverride.effectiveDwellSeconds(
            recordedDwellSeconds: currentSegment.durationSeconds,
            besideManifestFile: segmentManifestFileUrl
        )
        guard dwellSeconds < currentSegment.durationSeconds else {
            return
        }
        let dwellEndTime = CMTime(
            seconds: dwellSeconds,
            preferredTimescale: Self.boundaryTimescale
        )
        segmentDwellObserver = player.addBoundaryTimeObserver(
            forTimes: [NSValue(time: dwellEndTime)],
            queue: .main
        ) { [weak self] in
            self?.player.advanceToNextItem()
        }
    }

    private func removeSegmentDwellObserver() {
        guard let existingObserver = segmentDwellObserver else {
            return
        }
        player.removeTimeObserver(existingObserver)
        segmentDwellObserver = nil
    }
}
