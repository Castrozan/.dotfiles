import Foundation

struct AmbientCanvasRecordedSegment: Decodable {
    let file: String
    let durationSeconds: Double
}

struct AmbientCanvasRecordedSegmentManifest: Decodable {
    let segments: [AmbientCanvasRecordedSegment]

    static func load(fromManifestFileUrl manifestFileUrl: URL)
        -> AmbientCanvasRecordedSegmentManifest?
    {
        guard let manifestData = try? Data(contentsOf: manifestFileUrl) else {
            return nil
        }
        guard
            let decodedManifest = try? JSONDecoder().decode(
                AmbientCanvasRecordedSegmentManifest.self,
                from: manifestData
            )
        else {
            return nil
        }
        guard !decodedManifest.segments.isEmpty else {
            return nil
        }
        return decodedManifest
    }

    func segmentFileUrls(relativeTo manifestFileUrl: URL) -> [URL] {
        let containingDirectoryUrl = manifestFileUrl.deletingLastPathComponent()
        return segments.map { recordedSegment in
            containingDirectoryUrl.appendingPathComponent(recordedSegment.file)
        }
    }
}
