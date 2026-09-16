import AppKit

@main
enum LauncherTests {
  static func main() throws {
    _ = NSApplication.shared
    precondition(fuzzyMatch(item: "Visual Studio Code", query: "vsc"))
    precondition(fuzzyMatch(item: "Terminal", query: ""))
    precondition(!fuzzyMatch(item: "Terminal", query: "lat"))
    try LaunchHistoryTests.runAll()
    try LauncherCommandTests.runAll()
    PickerTests.runAll()
    try ApplicationCatalogTests.runAll()
    try LauncherSocketTests.runAll()
    print("Application launcher contracts passed")
  }
}
