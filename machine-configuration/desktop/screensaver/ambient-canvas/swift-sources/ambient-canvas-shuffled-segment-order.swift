import Foundation

final class AmbientCanvasShuffledSegmentOrder {
    private let segmentCount: Int
    private var remainingSegmentIndices: [Int] = []
    private var previouslyPlayedSegmentIndex: Int?

    init(segmentCount: Int) {
        self.segmentCount = segmentCount
    }

    func nextSegmentIndex() -> Int {
        if remainingSegmentIndices.isEmpty {
            refillAvoidingImmediateRepeat()
        }
        let chosenSegmentIndex = remainingSegmentIndices.removeFirst()
        previouslyPlayedSegmentIndex = chosenSegmentIndex
        return chosenSegmentIndex
    }

    private func refillAvoidingImmediateRepeat() {
        guard segmentCount > 0 else {
            return
        }
        var shuffledIndices = Array(0..<segmentCount).shuffled()
        if segmentCount > 1, shuffledIndices.first == previouslyPlayedSegmentIndex {
            shuffledIndices.swapAt(0, shuffledIndices.count - 1)
        }
        remainingSegmentIndices = shuffledIndices
    }
}
