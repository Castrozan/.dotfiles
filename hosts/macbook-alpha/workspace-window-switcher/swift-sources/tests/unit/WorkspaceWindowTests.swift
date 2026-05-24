import Foundation

enum WorkspaceWindowTests {
    static func runAll() {
        testFromAeroSpaceDictionaryParsesWellFormedInput()
        testFromAeroSpaceDictionaryReturnsNilWithoutWindowIdentifier()
        testFromAeroSpaceDictionaryDefaultsEmptyApplicationName()
        testFromAeroSpaceDictionaryDefaultsTitleToApplicationName()
    }

    static func testFromAeroSpaceDictionaryParsesWellFormedInput() {
        let dictionary: [String: Any] = [
            "window-id": 42,
            "app-name": "WezTerm",
            "window-title": "fish",
        ]
        let parsed = WorkspaceWindow.fromAeroSpaceDictionary(dictionary)
        TestAssertion.assertEqual(
            parsed,
            WorkspaceWindow(identifier: 42, applicationName: "WezTerm", title: "fish")
        )
    }

    static func testFromAeroSpaceDictionaryReturnsNilWithoutWindowIdentifier() {
        let dictionary: [String: Any] = ["app-name": "WezTerm", "window-title": "fish"]
        TestAssertion.assertNil(WorkspaceWindow.fromAeroSpaceDictionary(dictionary))
    }

    static func testFromAeroSpaceDictionaryDefaultsEmptyApplicationName() {
        let dictionary: [String: Any] = ["window-id": 1, "window-title": "fish"]
        let parsed = WorkspaceWindow.fromAeroSpaceDictionary(dictionary)
        TestAssertion.assertEqual(parsed?.applicationName, "")
    }

    static func testFromAeroSpaceDictionaryDefaultsTitleToApplicationName() {
        let dictionary: [String: Any] = ["window-id": 1, "app-name": "App"]
        let parsed = WorkspaceWindow.fromAeroSpaceDictionary(dictionary)
        TestAssertion.assertEqual(parsed?.title, "App")
    }
}
