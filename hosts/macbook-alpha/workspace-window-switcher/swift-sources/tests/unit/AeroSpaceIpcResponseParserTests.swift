import Foundation

enum AeroSpaceIpcResponseParserTests {
    static func runAll() {
        testParsesSingleResponseObject()
        testParsesFirstObjectFromConcatenatedResponses()
        testReturnsExitCodeAndStdoutFromSuccessResponse()
        testReturnsNonZeroExitCodeFromErrorResponse()
        testReturnsEmptyStdoutWhenAbsent()
        testReturnsNilForCompletelyInvalidInput()
        testIgnoresBracesInsideStringLiteralsWhenScanning()
    }

    static func testParsesSingleResponseObject() {
        let json = #"{"exitCode":0,"stdout":"ok","stderr":""}"#
        let parsed = AeroSpaceIpcResponseParser.parseFirstResponse(from: Data(json.utf8))
        TestAssertion.assertEqual(parsed, AeroSpaceIpcResponse(exitCode: 0, stdoutContent: "ok"))
    }

    static func testParsesFirstObjectFromConcatenatedResponses() {
        let first = #"{"exitCode":0,"stdout":"first","stderr":""}"#
        let second = #"{"exitCode":1,"stdout":"","stderr":"err"}"#
        let concatenated = Data((first + second).utf8)
        let parsed = AeroSpaceIpcResponseParser.parseFirstResponse(from: concatenated)
        TestAssertion.assertEqual(parsed, AeroSpaceIpcResponse(exitCode: 0, stdoutContent: "first"))
    }

    static func testReturnsExitCodeAndStdoutFromSuccessResponse() {
        let json = #"{"exitCode":0,"stdout":"[{\"window-id\":99}]","stderr":""}"#
        let parsed = AeroSpaceIpcResponseParser.parseFirstResponse(from: Data(json.utf8))
        TestAssertion.assertEqual(parsed?.exitCode, 0)
        TestAssertion.assertEqual(parsed?.stdoutContent, "[{\"window-id\":99}]")
    }

    static func testReturnsNonZeroExitCodeFromErrorResponse() {
        let json = #"{"exitCode":42,"stdout":"","stderr":"boom"}"#
        let parsed = AeroSpaceIpcResponseParser.parseFirstResponse(from: Data(json.utf8))
        TestAssertion.assertEqual(parsed?.exitCode, 42)
    }

    static func testReturnsEmptyStdoutWhenAbsent() {
        let json = #"{"exitCode":0,"stderr":""}"#
        let parsed = AeroSpaceIpcResponseParser.parseFirstResponse(from: Data(json.utf8))
        TestAssertion.assertEqual(parsed?.stdoutContent, "")
    }

    static func testReturnsNilForCompletelyInvalidInput() {
        TestAssertion.assertNil(AeroSpaceIpcResponseParser.parseFirstResponse(from: Data("not json".utf8)))
    }

    static func testIgnoresBracesInsideStringLiteralsWhenScanning() {
        let first = #"{"exitCode":0,"stdout":"contains } brace","stderr":""}"#
        let second = #"{"exitCode":1,"stdout":"","stderr":""}"#
        let concatenated = Data((first + second).utf8)
        let parsed = AeroSpaceIpcResponseParser.parseFirstResponse(from: concatenated)
        TestAssertion.assertEqual(parsed?.stdoutContent, "contains } brace")
    }
}
