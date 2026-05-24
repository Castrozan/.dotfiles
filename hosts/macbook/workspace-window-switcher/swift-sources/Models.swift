import Foundation

struct WorkspaceWindow: Equatable {
    let identifier: Int
    let applicationName: String
    let title: String

    static func fromAeroSpaceDictionary(_ dictionary: [String: Any]) -> WorkspaceWindow? {
        guard let identifier = dictionary["window-id"] as? Int else { return nil }
        let applicationName = (dictionary["app-name"] as? String) ?? ""
        let title = (dictionary["window-title"] as? String) ?? applicationName
        return WorkspaceWindow(identifier: identifier, applicationName: applicationName, title: title)
    }
}

enum SocketCommand: Equatable {
    case next
    case prev
    case commit
    case cancel
    case recordExternalFocus(windowIdentifier: Int)
}
