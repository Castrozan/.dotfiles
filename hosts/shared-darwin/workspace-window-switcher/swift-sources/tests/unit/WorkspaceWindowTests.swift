import Foundation

enum WorkspaceWindowTests {
    static func runAll() {
        testFromWindowDictionaryParsesWellFormedInput()
        testFromWindowDictionaryReturnsNilWithoutWindowIdentifier()
        testFromWindowDictionaryDefaultsEmptyApplicationName()
        testFromWindowDictionaryDefaultsTitleToApplicationName()
    }

    static func testFromWindowDictionaryParsesWellFormedInput() {
        let dictionary: [String: Any] = [
            "window-id": 42,
            "app-name": "WezTerm",
            "window-title": "fish",
        ]
        let parsed = WorkspaceWindow.fromWindowDictionary(dictionary)
        TestAssertion.assertEqual(
            parsed,
            WorkspaceWindow(identifier: 42, applicationName: "WezTerm", title: "fish")
        )
    }

    static func testFromWindowDictionaryReturnsNilWithoutWindowIdentifier() {
        let dictionary: [String: Any] = ["app-name": "WezTerm", "window-title": "fish"]
        TestAssertion.assertNil(WorkspaceWindow.fromWindowDictionary(dictionary))
    }

    static func testFromWindowDictionaryDefaultsEmptyApplicationName() {
        let dictionary: [String: Any] = ["window-id": 1, "window-title": "fish"]
        let parsed = WorkspaceWindow.fromWindowDictionary(dictionary)
        TestAssertion.assertEqual(parsed?.applicationName, "")
    }

    static func testFromWindowDictionaryDefaultsTitleToApplicationName() {
        let dictionary: [String: Any] = ["window-id": 1, "app-name": "App"]
        let parsed = WorkspaceWindow.fromWindowDictionary(dictionary)
        TestAssertion.assertEqual(parsed?.title, "App")
    }
}
