import AVFoundation
import AppKit

@main
struct AmbientCanvasVideoPresentationTest {
    static func main() {
        let manifestFileUrl = URL(fileURLWithPath: CommandLine.arguments[1])
        let manifest = AmbientCanvasRecordedSegmentManifest.load(
            fromManifestFileUrl: manifestFileUrl)!
        for segmentFileUrl in manifest.segmentFileUrls(relativeTo: manifestFileUrl) {
            createVideoSegment(at: segmentFileUrl)
        }
        let videoView = AmbientCanvasRecordedLoopVideoView(
            recordedSegmentManifestFileUrl: manifestFileUrl,
            playbackDwellOverrideFileUrl: manifestFileUrl.appendingPathExtension("dwell")
        )
        let playerLayer = videoView.layer!.sublayers![0] as! AVPlayerLayer
        let queuePlayer = playerLayer.player as! AVQueuePlayer

        videoView.pausePlayback()
        precondition(
            playerLayer.player === queuePlayer,
            "Brief occlusion must preserve the presentation for a quick return")
        videoView.resumePlayback()
        RunLoop.main.run(until: Date().addingTimeInterval(0.6))
        precondition(
            playerLayer.player === queuePlayer,
            "A canceled release must not detach a resumed presentation")
        waitForPlayback { queuePlayer.currentItem?.status == .readyToPlay }
        let queuedItems = queuePlayer.items()

        for _ in 0..<3 {
            videoView.pausePlayback()
            let pausedTime = queuePlayer.currentTime().seconds
            RunLoop.main.run(until: Date().addingTimeInterval(0.6))
            precondition(playerLayer.player == nil, "Hidden video must release its presentation")
            precondition(queuePlayer.rate == 0, "Hidden video must remain paused")
            precondition(queuePlayer.items() == queuedItems, "Pause must preserve the queue")
            precondition(abs(queuePlayer.currentTime().seconds - pausedTime) < 1.0 / 60)

            videoView.pausePlayback()
            precondition(playerLayer.player == nil, "Repeated pauses must remain detached")

            videoView.resumePlayback()
            precondition(
                playerLayer.player === queuePlayer, "Resume must reconnect the same player")
            precondition(queuePlayer.items() == queuedItems, "Resume must preserve the queue")

            videoView.resumePlayback()
            precondition(
                playerLayer.player === queuePlayer, "Repeated resumes must remain attached")
            waitForPlayback { queuePlayer.currentTime().seconds > pausedTime }
        }
        videoView.pausePlayback()
        print("Video presentation lifecycle passed")
    }

    private static func waitForPlayback(_ condition: () -> Bool) {
        let deadline = Date().addingTimeInterval(5)
        while !condition() && Date() < deadline {
            RunLoop.main.run(until: Date().addingTimeInterval(0.01))
        }
        precondition(condition(), "Video playback did not become ready within five seconds")
    }

    private static func createVideoSegment(at fileUrl: URL) {
        guard !FileManager.default.fileExists(atPath: fileUrl.path) else {
            return
        }
        let writer = try! AVAssetWriter(outputURL: fileUrl, fileType: .mp4)
        let input = AVAssetWriterInput(
            mediaType: .video,
            outputSettings: [
                AVVideoCodecKey: AVVideoCodecType.h264,
                AVVideoWidthKey: 64,
                AVVideoHeightKey: 64,
            ])
        let adaptor = AVAssetWriterInputPixelBufferAdaptor(
            assetWriterInput: input,
            sourcePixelBufferAttributes: [
                kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_32ARGB,
                kCVPixelBufferWidthKey as String: 64,
                kCVPixelBufferHeightKey as String: 64,
            ])
        writer.add(input)
        precondition(writer.startWriting())
        writer.startSession(atSourceTime: .zero)
        var pixelBuffer: CVPixelBuffer?
        precondition(
            CVPixelBufferPoolCreatePixelBuffer(nil, adaptor.pixelBufferPool!, &pixelBuffer)
                == kCVReturnSuccess)
        let buffer = pixelBuffer!
        CVPixelBufferLockBaseAddress(buffer, [])
        memset(CVPixelBufferGetBaseAddress(buffer), 0, CVPixelBufferGetDataSize(buffer))
        CVPixelBufferUnlockBaseAddress(buffer, [])
        for frameIndex in 0..<240 {
            while !input.isReadyForMoreMediaData {
                Thread.sleep(forTimeInterval: 0.001)
            }
            precondition(
                adaptor.append(
                    buffer, withPresentationTime: CMTime(value: Int64(frameIndex), timescale: 60)))
        }
        input.markAsFinished()
        let completion = DispatchSemaphore(value: 0)
        writer.finishWriting { completion.signal() }
        precondition(completion.wait(timeout: .now() + 5) == .success)
        precondition(writer.status == .completed)
    }
}
