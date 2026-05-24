import Foundation

enum AeroSpaceIpcRequestEncoderTests {
    static func runAll() {
        testEncodesArgumentsArray()
        testEncodesEmptyStdinField()
        testEncodesWindowIdAsExplicitNull()
        testEncodesWorkspaceAsExplicitNull()
        testProducesValidJsonForCommonCommand()
    }

    static func testEncodesArgumentsArray() {
        let encoded = AeroSpaceIpcRequestEncoder.encodeRequest(arguments: ["list-windows", "--focused"])
        let parsed = try! JSONSerialization.jsonObject(with: encoded!) as! [String: Any]
        TestAssertion.assertEqual(parsed["args"] as? [String] ?? [], ["list-windows", "--focused"])
    }

    static func testEncodesEmptyStdinField() {
        let encoded = AeroSpaceIpcRequestEncoder.encodeRequest(arguments: ["focus"])
        let parsed = try! JSONSerialization.jsonObject(with: encoded!) as! [String: Any]
        TestAssertion.assertEqual(parsed["stdin"] as? String, "")
    }

    static func testEncodesWindowIdAsExplicitNull() {
        let encoded = AeroSpaceIpcRequestEncoder.encodeRequest(arguments: ["focus"])
        let parsed = try! JSONSerialization.jsonObject(with: encoded!) as! [String: Any]
        TestAssertion.assertTrue(parsed["windowId"] is NSNull, "windowId should be JSON null")
    }

    static func testEncodesWorkspaceAsExplicitNull() {
        let encoded = AeroSpaceIpcRequestEncoder.encodeRequest(arguments: ["focus"])
        let parsed = try! JSONSerialization.jsonObject(with: encoded!) as! [String: Any]
        TestAssertion.assertTrue(parsed["workspace"] is NSNull, "workspace should be JSON null")
    }

    static func testProducesValidJsonForCommonCommand() {
        let encoded = AeroSpaceIpcRequestEncoder.encodeRequest(
            arguments: ["list-windows", "--workspace", "focused", "--json"]
        )
        TestAssertion.assertTrue(encoded != nil, "encoder should produce non-nil data")
        let asString = String(data: encoded!, encoding: .utf8)!
        TestAssertion.assertTrue(asString.contains("list-windows"), "encoded JSON contains command name")
        TestAssertion.assertTrue(asString.contains("\"stdin\""), "encoded JSON contains stdin field")
    }
}
