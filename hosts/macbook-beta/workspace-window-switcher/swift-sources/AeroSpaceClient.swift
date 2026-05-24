import Darwin
import Foundation

final class AeroSpaceSocketPathResolver {
    private var cachedSocketPath: String?

    func resolveSocketPath() -> String? {
        if cachedSocketPath == nil {
            cachedSocketPath = findSocketPathOnDisk()
        }
        return cachedSocketPath
    }

    func invalidateCachedSocketPath() {
        cachedSocketPath = nil
    }

    private func findSocketPathOnDisk() -> String? {
        let username = ProcessInfo.processInfo.environment["USER"] ?? NSUserName()
        let expectedSocketPath = "/tmp/bobko.aerospace-\(username).sock"
        if FileManager.default.fileExists(atPath: expectedSocketPath) {
            return expectedSocketPath
        }
        guard let directoryEntries = try? FileManager.default.contentsOfDirectory(atPath: "/tmp") else {
            return nil
        }
        let matchingFileName = directoryEntries.first { fileName in
            fileName.hasPrefix("bobko.aerospace-") && fileName.hasSuffix(".sock")
        }
        guard let matchedFileName = matchingFileName else { return nil }
        return "/tmp/\(matchedFileName)"
    }
}

final class AeroSpaceIpcClient {
    private let socketPathResolver: AeroSpaceSocketPathResolver
    private let connectionTimeoutSeconds: Int

    init(socketPathResolver: AeroSpaceSocketPathResolver, connectionTimeoutSeconds: Int) {
        self.socketPathResolver = socketPathResolver
        self.connectionTimeoutSeconds = connectionTimeoutSeconds
    }

    func sendRequestAndReadResponse(_ requestData: Data) -> Data? {
        guard let socketPath = socketPathResolver.resolveSocketPath() else { return nil }
        guard let descriptor = UnixSocketConnector.connectStreamSocket(
            toPath: socketPath,
            timeoutSeconds: connectionTimeoutSeconds
        ) else {
            socketPathResolver.invalidateCachedSocketPath()
            return nil
        }
        defer { Darwin.close(descriptor) }

        if !writeAllRequestBytes(requestData, toDescriptor: descriptor) {
            socketPathResolver.invalidateCachedSocketPath()
            return nil
        }
        _ = Darwin.shutdown(descriptor, SHUT_WR)
        return readUntilPeerCloses(descriptor: descriptor)
    }

    private func writeAllRequestBytes(_ requestData: Data, toDescriptor descriptor: Int32) -> Bool {
        let bytesWritten = requestData.withUnsafeBytes { rawBufferPointer -> Int in
            return Darwin.send(descriptor, rawBufferPointer.baseAddress, rawBufferPointer.count, 0)
        }
        return bytesWritten == requestData.count
    }

    private func readUntilPeerCloses(descriptor: Int32) -> Data {
        var responseData = Data()
        var readBuffer = [UInt8](repeating: 0, count: 4096)
        while true {
            let bytesRead = readBuffer.withUnsafeMutableBufferPointer { bufferPointer -> Int in
                return Darwin.recv(descriptor, bufferPointer.baseAddress, bufferPointer.count, 0)
            }
            if bytesRead <= 0 { break }
            responseData.append(readBuffer, count: bytesRead)
        }
        return responseData
    }
}

final class AeroSpaceWindowProvider: WindowProviding, WindowFocusing {
    private let ipcClient: AeroSpaceIpcClient

    init(ipcClient: AeroSpaceIpcClient) {
        self.ipcClient = ipcClient
    }

    func getFocusedWorkspaceWindows() -> [WorkspaceWindow] {
        let dictionaries = listWindowDictionaries(arguments: ["list-windows", "--workspace", "focused", "--json"])
        return dictionaries.compactMap(WorkspaceWindow.fromAeroSpaceDictionary)
    }

    func getFocusedWindowIdentifier() -> Int? {
        let dictionaries = listWindowDictionaries(arguments: ["list-windows", "--focused", "--json"])
        guard let firstDictionary = dictionaries.first else { return nil }
        return firstDictionary["window-id"] as? Int
    }

    func focusWindow(withIdentifier identifier: Int) {
        _ = executeCommand(arguments: ["focus", "--window-id", String(identifier)])
    }

    private func listWindowDictionaries(arguments: [String]) -> [[String: Any]] {
        guard let stdoutContent = executeCommand(arguments: arguments) else { return [] }
        guard let data = stdoutContent.data(using: .utf8) else { return [] }
        return (try? JSONSerialization.jsonObject(with: data) as? [[String: Any]]) ?? []
    }

    private func executeCommand(arguments: [String]) -> String? {
        guard let requestData = AeroSpaceIpcRequestEncoder.encodeRequest(arguments: arguments) else {
            return nil
        }
        guard let responseData = ipcClient.sendRequestAndReadResponse(requestData) else {
            return nil
        }
        guard let parsedResponse = AeroSpaceIpcResponseParser.parseFirstResponse(from: responseData) else {
            return nil
        }
        if parsedResponse.exitCode != 0 { return nil }
        return parsedResponse.stdoutContent
    }
}
