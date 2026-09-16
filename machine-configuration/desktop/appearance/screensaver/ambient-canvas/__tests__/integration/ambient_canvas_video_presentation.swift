import AVFoundation
import AppKit

@main
struct AmbientCanvasVideoPresentationTest {
    static func main() {
        let manifestFileUrl = URL(fileURLWithPath: CommandLine.arguments[1])
        let videoView = AmbientCanvasRecordedLoopVideoView(
            recordedSegmentManifestFileUrl: manifestFileUrl,
            playbackDwellOverrideFileUrl: manifestFileUrl.appendingPathExtension("dwell")
        )
        let playerLayer = videoView.layer!.sublayers![0] as! AVPlayerLayer
        let queuePlayer = playerLayer.player as! AVQueuePlayer
        let queuedItems = queuePlayer.items()

        for _ in 0..<3 {
            videoView.pausePlayback()
            precondition(playerLayer.player == nil, "Hidden video must release its presentation")
            precondition(queuePlayer.rate == 0, "Hidden video must remain paused")
            precondition(queuePlayer.items() == queuedItems, "Pause must preserve the queue")

            videoView.pausePlayback()
            precondition(playerLayer.player == nil, "Repeated pauses must remain detached")

            videoView.resumePlayback()
            precondition(
                playerLayer.player === queuePlayer, "Resume must reconnect the same player")
            precondition(queuePlayer.items() == queuedItems, "Resume must preserve the queue")

            videoView.resumePlayback()
            precondition(
                playerLayer.player === queuePlayer, "Repeated resumes must remain attached")
        }
        videoView.pausePlayback()
        print("Video presentation lifecycle passed")
    }
}
