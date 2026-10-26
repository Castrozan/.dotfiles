import Darwin
import Foundation

#if SWIFT_PACKAGE
  import DesktopCommandSockets
#endif

final class ApplicationLauncherDaemonCommandSocketServer {
  private let socketPath: String
  private let socketFileMode: mode_t
  private let datagramReadBufferSize: Int
  private let onCommandReceived: (String) -> Void

  init(
    socketPath: String,
    socketFileMode: mode_t,
    datagramReadBufferSize: Int,
    onCommandReceived: @escaping (String) -> Void
  ) {
    self.socketPath = socketPath
    self.socketFileMode = socketFileMode
    self.datagramReadBufferSize = datagramReadBufferSize
    self.onCommandReceived = onCommandReceived
  }

  func startReceivingDatagramsOnBackgroundThread() {
    DispatchQueue.global(qos: .userInteractive).async {
      self.runReceiveLoopUntilTerminated()
    }
  }

  private func runReceiveLoopUntilTerminated() {
    guard
      let serverDescriptor =
        ApplicationLauncherDaemonUnixDatagramSocketBinder
        .bindDatagramSocketAtPath(socketPath, fileMode: socketFileMode)
    else { exitSoLaunchdRestartsTheDaemon() }

    UnixDatagramCommandReceiver.receiveCommands(
      from: serverDescriptor,
      bufferSize: datagramReadBufferSize,
      onCommandReceived: onCommandReceived
    )
  }

  private func exitSoLaunchdRestartsTheDaemon() -> Never {
    FileHandle.standardError.write(Data("cannot listen on \(socketPath)\n".utf8))
    exit(EXIT_FAILURE)
  }
}
