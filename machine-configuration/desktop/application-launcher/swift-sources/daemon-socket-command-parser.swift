import Foundation

enum ParsedSocketCommand {
    case showPicker(perRequestProfileOutputFilePath: String?)
    case dumpDisplayLinesToFile(String)
    case dismissPicker
    case unknown
}

enum SocketCommandParser {
    static func parse(_ rawCommand: String) -> ParsedSocketCommand {
        let trimmedCommand = rawCommand.trimmingCharacters(in: .whitespacesAndNewlines)
        let commandParts = trimmedCommand.split(separator: " ", maxSplits: 1).map(String.init)
        guard let commandName = commandParts.first else { return .unknown }
        switch commandName {
        case "show":
            let argumentString = commandParts.count > 1 ? commandParts[1] : ""
            let profileFilePath = parseKeyValueArgument(argumentString, key: "profile")
            return .showPicker(perRequestProfileOutputFilePath: profileFilePath)
        case "dump-display-lines":
            let argumentString = commandParts.count > 1 ? commandParts[1] : ""
            let outputFilePath = argumentString.trimmingCharacters(in: .whitespacesAndNewlines)
            if outputFilePath.isEmpty { return .unknown }
            return .dumpDisplayLinesToFile(outputFilePath)
        case "dismiss":
            return .dismissPicker
        default:
            return .unknown
        }
    }

    private static func parseKeyValueArgument(_ argumentString: String, key: String) -> String? {
        let pairs = argumentString.split(separator: " ")
        for pair in pairs {
            let pairParts = pair.split(separator: "=", maxSplits: 1).map(String.init)
            if pairParts.count == 2 && pairParts[0] == key {
                return pairParts[1]
            }
        }
        return nil
    }
}
