import Foundation

enum SelectionIndexCalculator {
    static func initialIndexFromAccumulatedDirection(_ accumulatedDirection: Int, totalCount: Int) -> Int {
        if accumulatedDirection == 0 {
            return min(1, totalCount - 1)
        }
        let modulo = accumulatedDirection % totalCount
        return (modulo + totalCount) % totalCount
    }

    static func cycledIndex(currentValue: Int, direction: Int, totalCount: Int) -> Int {
        let modulo = (currentValue + direction) % totalCount
        return (modulo + totalCount) % totalCount
    }
}
