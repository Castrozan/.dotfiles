import Darwin
import Foundation

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
        guard let serverDescriptor = ApplicationLauncherDaemonUnixDatagramSocketBinder
            .bindDatagramSocketAtPath(socketPath, fileMode: socketFileMode) else { return }

        var readBuffer = [UInt8](repeating: 0, count: datagramReadBufferSize)
        while true {
            let bytesRead = readBuffer.withUnsafeMutableBufferPointer { bufferPointer -> Int in
                return Darwin.recvfrom(
                    serverDescriptor,
                    bufferPointer.baseAddress,
                    bufferPointer.count,
                    0,
                    nil,
                    nil
                )
            }
            if bytesRead <= 0 { continue }
            let receivedData = Data(readBuffer.prefix(bytesRead))
            guard let receivedString = String(data: receivedData, encoding: .utf8) else { continue }
            let trimmedPayload = receivedString.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmedPayload.isEmpty { continue }
            let normalizedCommand = extractCommandFromKarabinerJsonPayloadIfApplicable(trimmedPayload)
            if normalizedCommand.isEmpty { continue }
            onCommandReceived(normalizedCommand)
        }
    }

    private func extractCommandFromKarabinerJsonPayloadIfApplicable(_ payload: String) -> String {
        guard let payloadData = payload.data(using: .utf8) else { return payload }
        let jsonObject = try? JSONSerialization.jsonObject(
            with: payloadData,
            options: [.fragmentsAllowed]
        )
        if let stringPayload = jsonObject as? String {
            return stringPayload.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        return payload
    }
}
