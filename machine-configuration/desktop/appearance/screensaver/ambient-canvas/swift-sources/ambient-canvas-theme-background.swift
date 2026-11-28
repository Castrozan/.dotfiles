import AppKit

enum AmbientCanvasThemeBackground {
    static let colorsFilePathEnvironmentVariable = "AMBIENT_CANVAS_THEME_COLORS_PATH"
    static let pollIntervalSeconds: TimeInterval = 1

    static func colorsFileUrl(environment: [String: String]) -> URL? {
        guard let colorsFilePath = environment[colorsFilePathEnvironmentVariable],
            !colorsFilePath.isEmpty
        else {
            return nil
        }
        return URL(fileURLWithPath: colorsFilePath)
    }

    static func color(fromColorsFileContent colorsFileContent: String) -> NSColor? {
        let backgroundLinePattern = ##"(?m)^\s*background\s*=\s*"#([0-9a-fA-F]{6})""##
        guard
            let backgroundLineExpression = try? NSRegularExpression(
                pattern: backgroundLinePattern),
            let match = backgroundLineExpression.firstMatch(
                in: colorsFileContent,
                range: NSRange(colorsFileContent.startIndex..., in: colorsFileContent)),
            let hexRange = Range(match.range(at: 1), in: colorsFileContent),
            let hexValue = UInt32(colorsFileContent[hexRange], radix: 16)
        else {
            return nil
        }
        return NSColor(
            red: CGFloat((hexValue >> 16) & 0xff) / 255.0,
            green: CGFloat((hexValue >> 8) & 0xff) / 255.0,
            blue: CGFloat(hexValue & 0xff) / 255.0,
            alpha: 1.0
        )
    }

    static func resolveColor(readFrom colorsFileUrl: URL?) -> NSColor {
        guard let colorsFileUrl,
            let colorsFileContent = try? String(contentsOf: colorsFileUrl, encoding: .utf8),
            let themeColor = color(fromColorsFileContent: colorsFileContent)
        else {
            return AmbientCanvasPlayerWindowController.deepNavyBackgroundColor
        }
        return themeColor
    }
}
