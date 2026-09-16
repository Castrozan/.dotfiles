import Darwin
import Foundation

private final class CommandRecorder: SocketCommandHandling {
  var commands: [String] = []
  func handleNextCommand() { commands.append("next") }
  func handlePrevCommand() { commands.append("prev") }
  func handleCommitCommand() { commands.append("commit") }
  func handleCancelCommand() { commands.append("cancel") }
  func recordExternallyFocusedWindow(_ windowIdentifier: Int) {
    commands.append("focus \(windowIdentifier)")
  }
}

enum SocketTransportTests {
  static func runAll() throws {
    let directory = URL(fileURLWithPath: "/tmp").appendingPathComponent(UUID().uuidString)
    try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: directory) }
    let path = directory.appendingPathComponent("commands").path
    let tooLong = path + String(repeating: "x", count: 110)
    precondition(UnixSocketAddressBuilder.buildSocketAddress(forPath: tooLong) == nil)
    precondition(UnixSocketConnector.connectStreamSocket(toPath: tooLong, timeoutSeconds: 1) == nil)
    precondition(UnixSocketConnector.connectStreamSocket(toPath: path, timeoutSeconds: 1) == nil)
    precondition(
      UnixSocketBinder.bindDatagramSocket(
        atPath: tooLong, fileMode: 0o600, receiveBufferBytes: 4096) == nil)
    precondition(
      UnixSocketBinder.bindDatagramSocket(
        atPath: path + "/missing/socket", fileMode: 0o600, receiveBufferBytes: 4096) == nil)
    let stream = Darwin.socket(AF_UNIX, SOCK_STREAM, 0)
    defer { Darwin.close(stream) }
    var address = UnixSocketAddressBuilder.buildSocketAddress(forPath: path)!
    let length = socklen_t(MemoryLayout<sockaddr_un>.size)
    let bound = withUnsafePointer(to: &address) {
      $0.withMemoryRebound(to: sockaddr.self, capacity: 1) { Darwin.bind(stream, $0, length) }
    }
    precondition(bound == 0 && Darwin.listen(stream, 1) == 0)
    let client = UnixSocketConnector.connectStreamSocket(toPath: path, timeoutSeconds: 1)!
    Darwin.close(client)
    try FileManager.default.removeItem(atPath: path)
    let recorder = CommandRecorder()
    let dispatcher = SocketCommandMainThreadDispatcher(commandHandler: recorder)
    for command in [
      SocketCommand.next, .prev, .commit, .cancel, .recordExternalFocus(windowIdentifier: 42),
    ] {
      dispatcher.dispatchOnMainThread(command)
    }
    TestMainRunLoop.until { recorder.commands.count == 5 }
    precondition(recorder.commands == ["next", "prev", "commit", "cancel", "focus 42"])
    let server = CommandSocketServer(
      socketPath: path, socketFileMode: 0o600,
      datagramReadBufferSize: 4096, kernelReceiveBufferBytes: 4096
    ) { command in
      if let parsed = SocketCommandParser.parseTrimmedCommand(command) {
        dispatcher.dispatchOnMainThread(parsed)
      }
    }
    server.startReceivingDatagramsOnBackgroundThread()
    TestMainRunLoop.until { FileManager.default.fileExists(atPath: path) }
    let permissions =
      try FileManager.default.attributesOfItem(atPath: path)[.posixPermissions] as! NSNumber
    precondition(permissions.intValue == 0o600)
    let sender = Darwin.socket(AF_UNIX, SOCK_DGRAM, 0)
    defer { Darwin.close(sender) }
    for payload in [
      Data([0xff]), Data(), Data("   ".utf8), Data("\"  \"".utf8), Data(" next\n".utf8),
      Data("\" prev \"".utf8),
    ] {
      let sent = payload.withUnsafeBytes { bytes in
        withUnsafePointer(to: &address) { pointer in
          pointer.withMemoryRebound(to: sockaddr.self, capacity: 1) {
            Darwin.sendto(sender, bytes.baseAddress, bytes.count, 0, $0, length)
          }
        }
      }
      precondition(sent == payload.count)
    }
    TestMainRunLoop.until { recorder.commands.count == 7 }
    precondition(Array(recorder.commands.suffix(2)) == ["next", "prev"])
    withExtendedLifetime(server) {}
  }
}
