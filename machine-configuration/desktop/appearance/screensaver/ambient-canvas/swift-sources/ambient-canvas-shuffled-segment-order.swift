import Foundation

final class AmbientCanvasShuffledSegmentOrder {
    private let segmentIndicesByChoice: [[Int]]
    private var nextSegmentPositionByChoice: [Int]
    private var remainingChoiceIndices: [Int] = []
    private var previouslyPlayedChoiceIndex: Int?

    init(sequenceIdentifiers: [String?]) {
        var resolvedSegmentIndicesByChoice: [[Int]] = []
        var choiceIndexBySequence: [String: Int] = [:]
        for (segmentIndex, sequenceIdentifier) in sequenceIdentifiers.enumerated() {
            let choiceIndex: Int
            if let sequenceIdentifier, !sequenceIdentifier.isEmpty {
                if let existingChoiceIndex = choiceIndexBySequence[sequenceIdentifier] {
                    choiceIndex = existingChoiceIndex
                } else {
                    choiceIndex = resolvedSegmentIndicesByChoice.count
                    choiceIndexBySequence[sequenceIdentifier] = choiceIndex
                    resolvedSegmentIndicesByChoice.append([])
                }
            } else {
                choiceIndex = resolvedSegmentIndicesByChoice.count
                resolvedSegmentIndicesByChoice.append([])
            }
            resolvedSegmentIndicesByChoice[choiceIndex].append(segmentIndex)
        }
        segmentIndicesByChoice = resolvedSegmentIndicesByChoice
        nextSegmentPositionByChoice = Array(
            repeating: 0,
            count: resolvedSegmentIndicesByChoice.count
        )
    }

    func nextSegmentIndex() -> Int {
        if remainingChoiceIndices.isEmpty {
            refillAvoidingImmediateRepeat()
        }
        let chosenChoiceIndex = remainingChoiceIndices.removeFirst()
        let segmentIndices = segmentIndicesByChoice[chosenChoiceIndex]
        let segmentPosition = nextSegmentPositionByChoice[chosenChoiceIndex]
        let chosenSegmentIndex = segmentIndices[segmentPosition]
        nextSegmentPositionByChoice[chosenChoiceIndex] =
            (segmentPosition + 1) % segmentIndices.count
        previouslyPlayedChoiceIndex = chosenChoiceIndex
        return chosenSegmentIndex
    }

    private func refillAvoidingImmediateRepeat() {
        guard !segmentIndicesByChoice.isEmpty else {
            return
        }
        var shuffledIndices = Array(0..<segmentIndicesByChoice.count).shuffled()
        if
            segmentIndicesByChoice.count > 1,
            shuffledIndices.first == previouslyPlayedChoiceIndex
        {
            shuffledIndices.swapAt(0, shuffledIndices.count - 1)
        }
        remainingChoiceIndices = shuffledIndices
    }
}
