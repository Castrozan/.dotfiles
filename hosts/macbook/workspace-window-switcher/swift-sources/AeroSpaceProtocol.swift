import Foundation

enum AeroSpaceIpcRequestEncoder {
    static func encodeRequest(arguments: [String]) -> Data? {
        let requestObject: [String: Any] = [
            "args": arguments,
            "stdin": "",
            "windowId": NSNull(),
            "workspace": NSNull(),
        ]
        return try? JSONSerialization.data(withJSONObject: requestObject)
    }
}

struct AeroSpaceIpcResponse: Equatable {
    let exitCode: Int
    let stdoutContent: String
}

enum AeroSpaceIpcResponseParser {
    static func parseFirstResponse(from data: Data) -> AeroSpaceIpcResponse? {
        guard let firstObject = extractFirstJsonObject(from: data) else { return nil }
        let exitCode = (firstObject["exitCode"] as? Int) ?? 1
        let stdoutContent = (firstObject["stdout"] as? String) ?? ""
        return AeroSpaceIpcResponse(exitCode: exitCode, stdoutContent: stdoutContent)
    }

    private static func extractFirstJsonObject(from data: Data) -> [String: Any]? {
        if let singleObject = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
            return singleObject
        }
        guard let asString = String(data: data, encoding: .utf8) else { return nil }
        guard let endIndex = findEndOfFirstJsonObject(in: asString) else { return nil }
        let firstObjectSlice = asString[asString.startIndex..<endIndex]
        guard let firstObjectData = String(firstObjectSlice).data(using: .utf8) else { return nil }
        return (try? JSONSerialization.jsonObject(with: firstObjectData)) as? [String: Any]
    }

    private static func findEndOfFirstJsonObject(in jsonString: String) -> String.Index? {
        var openBraceDepth = 0
        var insideStringLiteral = false
        var previousCharacter: Character = " "
        for currentIndex in jsonString.indices {
            let currentCharacter = jsonString[currentIndex]
            if insideStringLiteral {
                if currentCharacter == "\"" && previousCharacter != "\\" {
                    insideStringLiteral = false
                }
            } else if currentCharacter == "\"" {
                insideStringLiteral = true
            } else if currentCharacter == "{" {
                openBraceDepth += 1
            } else if currentCharacter == "}" {
                openBraceDepth -= 1
                if openBraceDepth == 0 {
                    return jsonString.index(after: currentIndex)
                }
            }
            previousCharacter = currentCharacter
        }
        return nil
    }
}
