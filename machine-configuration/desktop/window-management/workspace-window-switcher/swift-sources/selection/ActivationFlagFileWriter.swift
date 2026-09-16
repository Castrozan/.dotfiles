import Foundation

final class ActivationFlagFileWriter: ActivationFlagWriting {
    private let flagFilePath: String

    init(flagFilePath: String) {
        self.flagFilePath = flagFilePath
    }

    func writeActivationFlag() {
        FileManager.default.createFile(atPath: flagFilePath, contents: nil)
    }

    func clearActivationFlag() {
        try? FileManager.default.removeItem(atPath: flagFilePath)
    }
}
