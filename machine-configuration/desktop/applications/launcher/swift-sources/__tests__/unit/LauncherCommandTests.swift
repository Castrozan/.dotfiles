import Foundation

enum LauncherCommandTests {
  static func runAll() throws {
    for command in ["", "unknown", "dump-display-lines", "dump-display-lines   "] {
      guard case .unknown = SocketCommandParser.parse(command) else { preconditionFailure(command) }
    }
    guard case .dismissPicker = SocketCommandParser.parse(" dismiss\n") else {
      preconditionFailure()
    }
    guard case .showPicker(nil) = SocketCommandParser.parse("show ignored invalid=x") else {
      preconditionFailure()
    }
    guard case .showPicker(let path) = SocketCommandParser.parse("show invalid=x profile=/tmp/a=b")
    else { preconditionFailure() }
    precondition(path == "/tmp/a=b")
    guard
      case .dumpDisplayLinesToFile(let output) = SocketCommandParser.parse(
        "dump-display-lines /tmp/a b\n")
    else { preconditionFailure() }
    precondition(output == "/tmp/a b")
    let file = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
    defer { try? FileManager.default.removeItem(at: file) }
    let profiler = PerRequestColdStartProfiler(
      outputFilePath: file.path, baselineNanoseconds: DispatchTime.now().uptimeNanoseconds)
    profiler.recordMilestone("request")
    profiler.recordMilestone("visible")
    let lines = try String(contentsOf: file, encoding: .utf8).split(separator: "\n")
    precondition(lines.count == 2)
    precondition(lines[0].hasSuffix("\trequest") && lines[1].hasSuffix("\tvisible"))
    precondition(Double(lines[0].split(separator: "\t")[0])! >= 0)
    try FileManager.default.removeItem(at: file)
    profiler.recordMilestone("removed")
    precondition(!FileManager.default.fileExists(atPath: file.path))
  }
}
