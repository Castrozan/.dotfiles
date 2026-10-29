import Foundation

@main
enum AmbientCanvasContracts {
  static func main() throws {
    let directory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: directory) }
    let manifest = directory.appendingPathComponent("segments.json")
    precondition(AmbientCanvasRecordedSegmentManifest.load(fromManifestFileUrl: manifest) == nil)
    for invalid in ["invalid", "{}", "{\"segments\":[]}", "{\"segments\":[{\"file\":\"a\"}]}"] {
      try invalid.write(to: manifest, atomically: true, encoding: .utf8)
      precondition(AmbientCanvasRecordedSegmentManifest.load(fromManifestFileUrl: manifest) == nil)
    }
    try "{\"segments\":[{\"file\":\"a.mp4\",\"durationSeconds\":30,\"sequence\":\"birds\"}]}"
      .write(to: manifest, atomically: true, encoding: .utf8)
    let loaded = AmbientCanvasRecordedSegmentManifest.load(fromManifestFileUrl: manifest)!
    precondition(loaded.segments[0].durationSeconds == 30)
    precondition(loaded.segments[0].sequence == "birds")
    precondition(
      loaded.segmentFileUrls(relativeTo: manifest) == [directory.appendingPathComponent("a.mp4")])
    let override = directory.appendingPathComponent("dwell")
    precondition(
      AmbientCanvasPlaybackDwellOverride.effectiveDwellSeconds(
        recordedDwellSeconds: 30, readFrom: override) == 30)
    for (content, expected) in [("garbage", 30.0), (" 5\n", 5.0), ("-1", 2.0), ("60", 30.0)] {
      try content.write(to: override, atomically: true, encoding: .utf8)
      precondition(
        AmbientCanvasPlaybackDwellOverride.effectiveDwellSeconds(
          recordedDwellSeconds: 30, readFrom: override) == expected)
    }
    let single = AmbientCanvasShuffledSegmentOrder(sequenceIdentifiers: ["sequence", "sequence"])
    precondition(
      (0..<3).map { _ in single.nextSegmentIndices() } == [[0, 1], [0, 1], [0, 1]])
    let order = AmbientCanvasShuffledSegmentOrder(sequenceIdentifiers: ["birds", "birds", nil, ""])
    var previousChoice: Int?
    var birdSegments: [Int] = []
    for _ in 0..<30 {
      var choices = Set<Int>()
      for _ in 0..<3 {
        let segmentIndices = order.nextSegmentIndices()
        let choice = segmentIndices[0] < 2 ? 0 : segmentIndices[0]
        precondition(choice != previousChoice)
        precondition(choices.insert(choice).inserted)
        precondition(segmentIndices == (choice == 0 ? [0, 1] : [choice]))
        if choice == 0 { birdSegments.append(contentsOf: segmentIndices) }
        previousChoice = choice
      }
      precondition(choices == [0, 2, 3])
    }
    precondition(birdSegments == Array(repeating: [0, 1], count: 30).flatMap { $0 })
    print("Ambient canvas manifest, dwell and shuffle contracts passed")
  }
}
