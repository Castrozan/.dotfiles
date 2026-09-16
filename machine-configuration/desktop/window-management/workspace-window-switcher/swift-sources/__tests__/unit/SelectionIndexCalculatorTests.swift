import Foundation

enum SelectionIndexCalculatorTests {
    static func runAll() {
        testInitialIndexWithZeroDirectionPicksSecondWindowWhenCountAtLeastTwo()
        testInitialIndexWithZeroDirectionPicksOnlyWindowWhenCountIsOne()
        testInitialIndexWithPositiveOneDirection()
        testInitialIndexWithNegativeOneDirectionWrapsToLast()
        testInitialIndexWithPositiveDirectionExceedingCountWrapsAround()
        testInitialIndexWithLargeNegativeDirectionWrapsCorrectly()
        testInitialIndexWithCountOneAlwaysReturnsZero()
        testCycledIndexForwardWithinBounds()
        testCycledIndexBackwardWithinBounds()
        testCycledIndexForwardWrapsPastEnd()
        testCycledIndexBackwardWrapsPastStart()
        testCycledIndexLargeForwardSteps()
        testCycledIndexLargeBackwardSteps()
    }

    static func testInitialIndexWithZeroDirectionPicksSecondWindowWhenCountAtLeastTwo() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(0, totalCount: 3),
            1
        )
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(0, totalCount: 2),
            1
        )
    }

    static func testInitialIndexWithZeroDirectionPicksOnlyWindowWhenCountIsOne() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(0, totalCount: 1),
            0
        )
    }

    static func testInitialIndexWithPositiveOneDirection() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(1, totalCount: 3),
            1
        )
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(1, totalCount: 5),
            1
        )
    }

    static func testInitialIndexWithNegativeOneDirectionWrapsToLast() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(-1, totalCount: 3),
            2
        )
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(-1, totalCount: 5),
            4
        )
    }

    static func testInitialIndexWithPositiveDirectionExceedingCountWrapsAround() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(5, totalCount: 3),
            2
        )
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(7, totalCount: 3),
            1
        )
    }

    static func testInitialIndexWithLargeNegativeDirectionWrapsCorrectly() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(-5, totalCount: 3),
            1
        )
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(-7, totalCount: 3),
            2
        )
    }

    static func testInitialIndexWithCountOneAlwaysReturnsZero() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(1, totalCount: 1),
            0
        )
        TestAssertion.assertEqual(
            SelectionIndexCalculator.initialIndexFromAccumulatedDirection(-1, totalCount: 1),
            0
        )
    }

    static func testCycledIndexForwardWithinBounds() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.cycledIndex(currentValue: 0, direction: 1, totalCount: 3),
            1
        )
        TestAssertion.assertEqual(
            SelectionIndexCalculator.cycledIndex(currentValue: 1, direction: 1, totalCount: 3),
            2
        )
    }

    static func testCycledIndexBackwardWithinBounds() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.cycledIndex(currentValue: 2, direction: -1, totalCount: 3),
            1
        )
    }

    static func testCycledIndexForwardWrapsPastEnd() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.cycledIndex(currentValue: 2, direction: 1, totalCount: 3),
            0
        )
    }

    static func testCycledIndexBackwardWrapsPastStart() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.cycledIndex(currentValue: 0, direction: -1, totalCount: 3),
            2
        )
    }

    static func testCycledIndexLargeForwardSteps() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.cycledIndex(currentValue: 0, direction: 7, totalCount: 3),
            1
        )
    }

    static func testCycledIndexLargeBackwardSteps() {
        TestAssertion.assertEqual(
            SelectionIndexCalculator.cycledIndex(currentValue: 0, direction: -7, totalCount: 3),
            2
        )
    }
}
