import Darwin
import Foundation

public enum UnixDatagramCommandReceiver {
  public static func receiveCommands(
    from socketDescriptor: Int32,
    bufferSize: Int,
    onCommandReceived: (String) -> Void
  ) {
    var readBuffer = [UInt8](repeating: 0, count: bufferSize)
    while true {
      guard let command = receiveCommand(from: socketDescriptor, into: &readBuffer) else {
        continue
      }
      onCommandReceived(command)
    }
  }

  private static func receiveCommand(
    from socketDescriptor: Int32,
    into readBuffer: inout [UInt8]
  ) -> String? {
    let bytesRead = readBuffer.withUnsafeMutableBufferPointer { bufferPointer in
      Darwin.recvfrom(
        socketDescriptor, bufferPointer.baseAddress, bufferPointer.count, 0, nil, nil)
    }
    guard bytesRead > 0,
      let payload = String(bytes: readBuffer.prefix(bytesRead), encoding: .utf8)
    else { return nil }
    let trimmedPayload = payload.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !trimmedPayload.isEmpty else { return nil }
    let object = try? JSONSerialization.jsonObject(
      with: Data(trimmedPayload.utf8), options: [.fragmentsAllowed])
    let command = (object as? String ?? trimmedPayload).trimmingCharacters(
      in: .whitespacesAndNewlines)
    return command.isEmpty ? nil : command
  }
}
