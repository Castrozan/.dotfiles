import Foundation

enum SocketCommandParser {
    static let externalFocusCommandPrefix = "focus:"

    static func parseTrimmedCommand(_ trimmedCommand: String) -> SocketCommand? {
        if trimmedCommand.hasPrefix(externalFocusCommandPrefix) {
            let identifierString = String(trimmedCommand.dropFirst(externalFocusCommandPrefix.count))
            guard let identifier = Int(identifierString) else { return nil }
            return .recordExternalFocus(windowIdentifier: identifier)
        }
        switch trimmedCommand {
        case "next": return .next
        case "prev": return .prev
        case "commit": return .commit
        case "cancel": return .cancel
        default: return nil
        }
    }
}
