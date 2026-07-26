import Foundation

struct AmbientCanvasRecordedLoopSegment: Decodable {
    let startSeconds: Double
    let durationSeconds: Double

    var endSeconds: Double {
        return startSeconds + durationSeconds
    }
}

struct AmbientCanvasRecordedLoopSegmentTable: Decodable {
    let segments: [AmbientCanvasRecordedLoopSegment]

    static func loadAdjacentToRecordedLoop(_ recordedLoopFileUrl: URL)
        -> AmbientCanvasRecordedLoopSegmentTable?
    {
        let segmentTableUrl = recordedLoopFileUrl
            .deletingLastPathComponent()
            .appendingPathComponent("loop.segments.json")
        guard let segmentTableData = try? Data(contentsOf: segmentTableUrl) else {
            return nil
        }
        guard
            let decodedTable = try? JSONDecoder().decode(
                AmbientCanvasRecordedLoopSegmentTable.self,
                from: segmentTableData
            )
        else {
            return nil
        }
        guard decodedTable.segments.count > 1 else {
            return nil
        }
        return decodedTable
    }
}
