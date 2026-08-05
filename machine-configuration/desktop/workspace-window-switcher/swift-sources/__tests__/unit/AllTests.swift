import Foundation

@main
struct AllTestsRunner {
    static func main() {
        WorkspaceWindowTests.runAll()
        SelectionIndexCalculatorTests.runAll()
        MostRecentlyUsedWindowTrackerTests.runAll()
        SocketCommandParserTests.runAll()
        print("ALL SWIFT LOGIC TESTS PASSED")
    }
}
