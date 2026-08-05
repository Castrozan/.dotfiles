import Darwin
import Foundation

enum ApplicationLauncherDaemonUnixDatagramSocketBinder {
    static func bindDatagramSocketAtPath(_ path: String, fileMode: mode_t) -> Int32? {
        try? FileManager.default.removeItem(atPath: path)

        let descriptor = Darwin.socket(AF_UNIX, SOCK_DGRAM, 0)
        if descriptor < 0 { return nil }

        var address = sockaddr_un()
        address.sun_family = sa_family_t(AF_UNIX)
        let pathBytesWithNullTerminator = path.utf8CString
        if pathBytesWithNullTerminator.count > MemoryLayout.size(ofValue: address.sun_path) {
            Darwin.close(descriptor)
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
