import Foundation

enum TestAssertion {
    static func assertEqual<T: Equatable>(
        _ actualValue: T,
        _ expectedValue: T,
        file: StaticString = #file,
        line: UInt = #line
    ) {
        if actualValue != expectedValue {
            print("FAIL [\(file):\(line)] expected \(expectedValue), got \(actualValue)")
            exit(1)
        }
    }

    static func assertTrue(
        _ condition: Bool,
        _ message: String = "",
        file: StaticString = #file,
        line: UInt = #line
    ) {
        if !condition {
            print("FAIL [\(file):\(line)] \(message)")
            exit(1)
        }
    }

    static func assertNil<T>(
        _ value: T?,
        file: StaticString = #file,
        line: UInt = #line
    ) {
        if value != nil {
            print("FAIL [\(file):\(line)] expected nil, got \(String(describing: value))")
            exit(1)
        }
    }
}
