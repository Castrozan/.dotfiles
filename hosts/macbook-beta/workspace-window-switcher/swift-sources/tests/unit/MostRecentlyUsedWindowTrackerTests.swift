import Foundation

enum MostRecentlyUsedWindowTrackerTests {
    static let windowAlpha = WorkspaceWindow(identifier: 100, applicationName: "Alpha", title: "alpha")
    static let windowBeta = WorkspaceWindow(identifier: 200, applicationName: "Beta", title: "beta")
    static let windowGamma = WorkspaceWindow(identifier: 300, applicationName: "Gamma", title: "gamma")

    static func runAll() {
        testEmptyTrackerPreservesInputOrder()
        testRecordingFocusedWindowPlacesItFirstInSort()
        testMostRecentlyRecordedAppearsFirst()
        testRecordingAlreadyTrackedWindowMovesItToFront()
        testWindowsNotInMruFallToEndOfSortedOutput()
        testRemoveStaleDropsIdentifiersNotInCurrentSet()
        testRemoveStaleKeepsRelativeOrderOfSurvivors()
        testStableSortPreservesInputOrderForEqualPositions()
    }

    static func testEmptyTrackerPreservesInputOrder() {
        let tracker = MostRecentlyUsedWindowTracker()
        let sorted = tracker.sortWindowsByRecency([windowAlpha, windowBeta, windowGamma])
        TestAssertion.assertEqual(sorted.map { $0.identifier }, [100, 200, 300])
    }

    static func testRecordingFocusedWindowPlacesItFirstInSort() {
        let tracker = MostRecentlyUsedWindowTracker()
        tracker.recordFocusedWindow(200)
        let sorted = tracker.sortWindowsByRecency([windowAlpha, windowBeta, windowGamma])
        TestAssertion.assertEqual(sorted.map { $0.identifier }, [200, 100, 300])
    }

    static func testMostRecentlyRecordedAppearsFirst() {
        let tracker = MostRecentlyUsedWindowTracker()
        tracker.recordFocusedWindow(100)
        tracker.recordFocusedWindow(200)
        tracker.recordFocusedWindow(300)
        let sorted = tracker.sortWindowsByRecency([windowAlpha, windowBeta, windowGamma])
        TestAssertion.assertEqual(sorted.map { $0.identifier }, [300, 200, 100])
    }

    static func testRecordingAlreadyTrackedWindowMovesItToFront() {
        let tracker = MostRecentlyUsedWindowTracker()
        tracker.recordFocusedWindow(100)
        tracker.recordFocusedWindow(200)
        tracker.recordFocusedWindow(100)
        let sorted = tracker.sortWindowsByRecency([windowAlpha, windowBeta])
        TestAssertion.assertEqual(sorted.map { $0.identifier }, [100, 200])
    }

    static func testWindowsNotInMruFallToEndOfSortedOutput() {
        let tracker = MostRecentlyUsedWindowTracker()
        tracker.recordFocusedWindow(200)
        let sorted = tracker.sortWindowsByRecency([windowAlpha, windowBeta, windowGamma])
        TestAssertion.assertEqual(sorted[0].identifier, 200)
        let trailingIdentifiers = Set(sorted.dropFirst().map { $0.identifier })
        TestAssertion.assertEqual(trailingIdentifiers, Set([100, 300]))
    }

    static func testRemoveStaleDropsIdentifiersNotInCurrentSet() {
        let tracker = MostRecentlyUsedWindowTracker()
        tracker.recordFocusedWindow(100)
        tracker.recordFocusedWindow(200)
        tracker.recordFocusedWindow(300)
        tracker.removeStaleWindowIdentifiers(currentWindowIdentifiers: Set([200, 300]))
        let sorted = tracker.sortWindowsByRecency([windowAlpha, windowBeta, windowGamma])
        TestAssertion.assertEqual(sorted.map { $0.identifier }, [300, 200, 100])
    }

    static func testRemoveStaleKeepsRelativeOrderOfSurvivors() {
        let tracker = MostRecentlyUsedWindowTracker()
        tracker.recordFocusedWindow(100)
        tracker.recordFocusedWindow(200)
        tracker.recordFocusedWindow(300)
        tracker.removeStaleWindowIdentifiers(currentWindowIdentifiers: Set([100, 300]))
        let sorted = tracker.sortWindowsByRecency([windowAlpha, windowGamma])
        TestAssertion.assertEqual(sorted.map { $0.identifier }, [300, 100])
    }

    static func testStableSortPreservesInputOrderForEqualPositions() {
        let tracker = MostRecentlyUsedWindowTracker()
        tracker.recordFocusedWindow(100)
        let sorted = tracker.sortWindowsByRecency([windowBeta, windowGamma])
        TestAssertion.assertEqual(sorted.map { $0.identifier }, [200, 300])
    }
}
