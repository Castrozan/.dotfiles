import Foundation

@main
struct AllTestsRunner {
    static func main() {
        WorkspaceWindowTests.runAll()
        SelectionIndexCalculatorTests.runAll()
        MostRecentlyUsedWindowTrackerTests.runAll()
        SocketCommandParserTests.runAll()
        AeroSpaceIpcRequestEncoderTests.runAll()
        AeroSpaceIpcResponseParserTests.runAll()
        print("ALL SWIFT LOGIC TESTS PASSED")
    }
}
