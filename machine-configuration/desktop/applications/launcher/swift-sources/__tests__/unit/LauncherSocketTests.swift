import Darwin
import Foundation

enum LauncherSocketTests {
  static func runAll() throws {
    let directory = URL(fileURLWithPath: "/tmp").appendingPathComponent(UUID().uuidString)
    try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
    defer { try? FileManager.default.removeItem(at: directory) }
    let path = directory.appendingPathComponent("commands").path
    precondition(
      ApplicationLauncherDaemonUnixDatagramSocketBinder.bindDatagramSocketAtPath(
        path + String(repeating: "x", count: 110), fileMode: 0o600) == nil)
    precondition(
      ApplicationLauncherDaemonUnixDatagramSocketBinder.bindDatagramSocketAtPath(
        path + "/missing/socket", fileMode: 0o600) == nil)
    let received = DispatchSemaphore(value: 0)
    let lock = NSLock()
    var commands: [String] = []
    let server = ApplicationLauncherDaemonCommandSocketServer(
      socketPath: path, socketFileMode: 0o600,
      datagramReadBufferSize: 4096
    ) { command in
      lock.lock()
      commands.append(command)
      lock.unlock()
      received.signal()
    }
    server.startReceivingDatagramsOnBackgroundThread()
    let deadline = Date().addingTimeInterval(3)
    while !FileManager.default.fileExists(atPath: path) && Date() < deadline {
      Thread.sleep(forTimeInterval: 0.002)
    }
    let permissions =
      try FileManager.default.attributesOfItem(atPath: path)[.posixPermissions] as! NSNumber
    precondition(permissions.intValue == 0o600)
    var address = sockaddr_un()
    address.sun_family = sa_family_t(AF_UNIX)
    withUnsafeMutablePointer(to: &address.sun_path) { pointer in
      pointer.withMemoryRebound(to: CChar.self, capacity: 104) { destination in
        path.withCString { source in _ = strcpy(destination, source) }
      }
    }
    let sender = Darwin.socket(AF_UNIX, SOCK_DGRAM, 0)
    defer { Darwin.close(sender) }
    for payload in [
      Data([0xff]), Data(), Data("  ".utf8), Data("\" \"".utf8), Data(" show\n".utf8),
      Data("\" dismiss \"".utf8),
    ] {
      let sent = payload.withUnsafeBytes { bytes in
        withUnsafePointer(to: &address) { pointer in
          pointer.withMemoryRebound(to: sockaddr.self, capacity: 1) {
            Darwin.sendto(
              sender, bytes.baseAddress, bytes.count, 0, $0,
              socklen_t(MemoryLayout<sockaddr_un>.size))
          }
        }
      }
      precondition(sent == payload.count)
    }
    precondition(received.wait(timeout: .now() + 3) == .success)
    precondition(received.wait(timeout: .now() + 3) == .success)
    lock.lock()
    precondition(commands == ["show", "dismiss"])
    lock.unlock()
    withExtendedLifetime(server) {}
  }
}
