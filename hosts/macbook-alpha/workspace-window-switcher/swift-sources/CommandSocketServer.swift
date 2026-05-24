import Darwin
import Foundation

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
        switch command {
        case .next: commandHandler.handleNextCommand()
        case .prev: commandHandler.handlePrevCommand()
        case .commit: commandHandler.handleCommitCommand()
        case .cancel: commandHandler.handleCancelCommand()
        case .recordExternalFocus(let windowIdentifier):
            commandHandler.recordExternallyFocusedWindow(windowIdentifier)
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
        guard let serverDescriptor = UnixSocketBinder.bindDatagramSocket(
            atPath: socketPath,
            fileMode: socketFileMode,
            receiveBufferBytes: kernelReceiveBufferBytes
        ) else { return }

        var readBuffer = [UInt8](repeating: 0, count: datagramReadBufferSize)
        while true {
            let bytesRead = readBuffer.withUnsafeMutableBufferPointer { bufferPointer -> Int in
                return Darwin.recvfrom(serverDescriptor, bufferPointer.baseAddress, bufferPointer.count, 0, nil, nil)
            }
            if bytesRead <= 0 { continue }
            let receivedData = Data(readBuffer.prefix(bytesRead))
            guard let receivedString = String(data: receivedData, encoding: .utf8) else { continue }
            let trimmedPayload = receivedString.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmedPayload.isEmpty { continue }
            let normalizedCommand = extractCommandFromKarabinerPayload(trimmedPayload)
            if normalizedCommand.isEmpty { continue }
            onCommandReceived(normalizedCommand)
        }
    }

    private func extractCommandFromKarabinerPayload(_ payload: String) -> String {
        guard let payloadData = payload.data(using: .utf8) else { return payload }
        let jsonObject = try? JSONSerialization.jsonObject(with: payloadData, options: [.fragmentsAllowed])
        if let stringPayload = jsonObject as? String {
            return stringPayload.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return payload
    }
}
