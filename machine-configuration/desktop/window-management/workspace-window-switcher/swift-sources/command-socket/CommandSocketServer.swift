import Darwin
import Foundation

#if SWIFT_PACKAGE
  import DesktopCommandSockets
#endif

final class SocketCommandMainThreadDispatcher {
  private let commandHandler: SocketCommandHandling

  init(commandHandler: SocketCommandHandling) {
    self.commandHandler = commandHandler
  }

  func dispatchOnMainThread(_ command: SocketCommand) {
    DispatchQueue.main.async { [weak self] in
      guard let strongSelf = self else { return }
      strongSelf.executeCommandOnMainThread(command)
    }
  }

  private func executeCommandOnMainThread(_ command: SocketCommand) {
    if case .recordExternalFocus(let windowIdentifier) = command {
      commandHandler.recordExternallyFocusedWindow(windowIdentifier)
      return
    }
    executeNavigationCommand(command)
  }

  private func executeNavigationCommand(_ command: SocketCommand) {
    switch command {
    case .next: commandHandler.handleNextCommand()
    case .prev: commandHandler.handlePrevCommand()
    case .commit: commandHandler.handleCommitCommand()
    case .cancel: commandHandler.handleCancelCommand()
    default: return
    }
  }
}

final class CommandSocketServer {
  private let socketPath: String
  private let socketFileMode: mode_t
  private let datagramReadBufferSize: Int
  private let kernelReceiveBufferBytes: Int32
  private let onCommandReceived: (String) -> Void

  init(
    socketPath: String,
    socketFileMode: mode_t,
    datagramReadBufferSize: Int,
    kernelReceiveBufferBytes: Int32,
    onCommandReceived: @escaping (String) -> Void
  ) {
    self.socketPath = socketPath
    self.socketFileMode = socketFileMode
    self.datagramReadBufferSize = datagramReadBufferSize
    self.kernelReceiveBufferBytes = kernelReceiveBufferBytes
    self.onCommandReceived = onCommandReceived
  }

  func startReceivingDatagramsOnBackgroundThread() {
    DispatchQueue.global(qos: .userInteractive).async { [weak self] in
      self?.runReceiveLoopUntilTerminated()
    }
  }

  private func runReceiveLoopUntilTerminated() {
    guard
      let serverDescriptor = UnixSocketBinder.bindDatagramSocket(
        atPath: socketPath,
        fileMode: socketFileMode,
        receiveBufferBytes: kernelReceiveBufferBytes
      )
    else { return }

    UnixDatagramCommandReceiver.receiveCommands(
      from: serverDescriptor,
      bufferSize: datagramReadBufferSize,
      onCommandReceived: onCommandReceived)
  }
}
