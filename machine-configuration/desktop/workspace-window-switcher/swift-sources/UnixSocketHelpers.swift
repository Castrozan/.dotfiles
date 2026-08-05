import Darwin
import Foundation

enum UnixSocketAddressBuilder {
    static func buildSocketAddress(forPath path: String) -> sockaddr_un? {
        var address = sockaddr_un()
        address.sun_family = sa_family_t(AF_UNIX)
        let pathBytesWithNullTerminator = path.utf8CString
        if pathBytesWithNullTerminator.count > MemoryLayout.size(ofValue: address.sun_path) {
            return nil
        }
        withUnsafeMutablePointer(to: &address.sun_path) { sunPathPointer in
            sunPathPointer.withMemoryRebound(
                to: CChar.self,
                capacity: pathBytesWithNullTerminator.count
            ) { typedDestinationPointer in
                pathBytesWithNullTerminator.withUnsafeBufferPointer { sourceBufferPointer in
                    typedDestinationPointer.update(
                        from: sourceBufferPointer.baseAddress!,
                        count: pathBytesWithNullTerminator.count
                    )
                }
            }
        }
        return address
    }
}

enum UnixSocketConnector {
    static func connectStreamSocket(toPath path: String, timeoutSeconds: Int) -> Int32? {
        let descriptor = Darwin.socket(AF_UNIX, SOCK_STREAM, 0)
        if descriptor < 0 { return nil }

        var sendReceiveTimeout = timeval(tv_sec: timeoutSeconds, tv_usec: 0)
        let timevalLength = socklen_t(MemoryLayout<timeval>.size)
        _ = Darwin.setsockopt(descriptor, SOL_SOCKET, SO_RCVTIMEO, &sendReceiveTimeout, timevalLength)
        _ = Darwin.setsockopt(descriptor, SOL_SOCKET, SO_SNDTIMEO, &sendReceiveTimeout, timevalLength)

        guard var address = UnixSocketAddressBuilder.buildSocketAddress(forPath: path) else {
            Darwin.close(descriptor)
            return nil
        }
        let addressLength = socklen_t(MemoryLayout<sockaddr_un>.size)
        let connectResult = withUnsafePointer(to: &address) { addressPointer -> Int32 in
            return addressPointer.withMemoryRebound(to: sockaddr.self, capacity: 1) { sockaddrPointer in
                return Darwin.connect(descriptor, sockaddrPointer, addressLength)
            }
        }
        if connectResult < 0 {
            Darwin.close(descriptor)
            return nil
        }
        return descriptor
    }
}

enum UnixSocketBinder {
    static func bindDatagramSocket(
        atPath path: String,
        fileMode: mode_t,
        receiveBufferBytes: Int32
    ) -> Int32? {
        try? FileManager.default.removeItem(atPath: path)

        let descriptor = Darwin.socket(AF_UNIX, SOCK_DGRAM, 0)
        if descriptor < 0 { return nil }

        var requestedReceiveBufferBytes = receiveBufferBytes
        _ = Darwin.setsockopt(
            descriptor,
            SOL_SOCKET,
            SO_RCVBUF,
            &requestedReceiveBufferBytes,
            socklen_t(MemoryLayout<Int32>.size)
        )

        guard var address = UnixSocketAddressBuilder.buildSocketAddress(forPath: path) else {
            Darwin.close(descriptor)
            return nil
        }
        let addressLength = socklen_t(MemoryLayout<sockaddr_un>.size)
        let bindResult = withUnsafePointer(to: &address) { addressPointer -> Int32 in
            return addressPointer.withMemoryRebound(to: sockaddr.self, capacity: 1) { sockaddrPointer in
                return Darwin.bind(descriptor, sockaddrPointer, addressLength)
            }
        }
        if bindResult < 0 {
            Darwin.close(descriptor)
            return nil
        }
        path.withCString { pathCString in
            _ = Darwin.chmod(pathCString, fileMode)
        }
        return descriptor
    }
}
