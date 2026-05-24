import Foundation

enum SocketCommandParserTests {
    static func runAll() {
        testParsesNext()
        testParsesPrev()
        testParsesCommit()
        testParsesCancel()
        testParsesFocusWithValidIdentifier()
        testParsesFocusWithNegativeIdentifier()
        testReturnsNilForFocusWithNonNumericIdentifier()
        testReturnsNilForFocusWithEmptyIdentifier()
        testReturnsNilForUnknownCommand()
        testReturnsNilForEmptyString()
    }

    static func testParsesNext() {
        TestAssertion.assertEqual(SocketCommandParser.parseTrimmedCommand("next"), .next)
    }

    static func testParsesPrev() {
        TestAssertion.assertEqual(SocketCommandParser.parseTrimmedCommand("prev"), .prev)
    }

    static func testParsesCommit() {
        TestAssertion.assertEqual(SocketCommandParser.parseTrimmedCommand("commit"), .commit)
    }

    static func testParsesCancel() {
        TestAssertion.assertEqual(SocketCommandParser.parseTrimmedCommand("cancel"), .cancel)
    }

    static func testParsesFocusWithValidIdentifier() {
        TestAssertion.assertEqual(
            SocketCommandParser.parseTrimmedCommand("focus:12345"),
            .recordExternalFocus(windowIdentifier: 12345)
        )
    }

    static func testParsesFocusWithNegativeIdentifier() {
        TestAssertion.assertEqual(
            SocketCommandParser.parseTrimmedCommand("focus:-7"),
            .recordExternalFocus(windowIdentifier: -7)
        )
    }

    static func testReturnsNilForFocusWithNonNumericIdentifier() {
        TestAssertion.assertNil(SocketCommandParser.parseTrimmedCommand("focus:abc"))
    }

    static func testReturnsNilForFocusWithEmptyIdentifier() {
        TestAssertion.assertNil(SocketCommandParser.parseTrimmedCommand("focus:"))
    }

    static func testReturnsNilForUnknownCommand() {
        TestAssertion.assertNil(SocketCommandParser.parseTrimmedCommand("explode"))
    }

    static func testReturnsNilForEmptyString() {
        TestAssertion.assertNil(SocketCommandParser.parseTrimmedCommand(""))
    }
}
