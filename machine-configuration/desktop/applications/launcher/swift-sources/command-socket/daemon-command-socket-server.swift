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
    DispatchQueue.global(qos: .userInteractive).async { [weak self] in
      self?.runReceiveLoopUntilTerminated()
    }
  }

  private func runReceiveLoopUntilTerminated() {
    guard
      let serverDescriptor =
        ApplicationLauncherDaemonUnixDatagramSocketBinder
        .bindDatagramSocketAtPath(socketPath, fileMode: socketFileMode)
    else { return }

    UnixDatagramCommandReceiver.receiveCommands(
      from: serverDescriptor,
      bufferSize: datagramReadBufferSize,
      onCommandReceived: onCommandReceived
    )
  }
}
