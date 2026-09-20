import AppKit

@main
struct AllTestsRunner {
  static func main() throws {
    _ = NSApplication.shared
    WorkspaceWindowTests.runAll()
    SelectionIndexCalculatorTests.runAll()
    MostRecentlyUsedWindowTrackerTests.runAll()
    SocketCommandParserTests.runAll()
    StateMachineTests.runAll()
    StaleActivationTests.runAll()
    OverlayTests.runAll()
    try ActivationPersistenceTests.runAll()
    try SocketTransportTests.runAll()
    print("ALL SWIFT LOGIC TESTS PASSED")
  }
}
