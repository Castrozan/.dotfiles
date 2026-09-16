import QtQuick
import QtTest

OnScreenDisplayFixture {
    id: root

    TestCase {
        name: "OsdContentClampedFraction"

        function test_normal_value_within_range() {
            fuzzyCompare(osdContent.computeClampedFraction(50), 0.5, 0.001);
        }

        function test_zero_value() {
            fuzzyCompare(osdContent.computeClampedFraction(0), 0.0, 0.001);
        }

        function test_100_value() {
            fuzzyCompare(osdContent.computeClampedFraction(100), 1.0, 0.001);
        }

        function test_over_100_clamped_to_1() {
            fuzzyCompare(osdContent.computeClampedFraction(150), 1.0, 0.001);
        }

        function test_25_percent() {
            fuzzyCompare(osdContent.computeClampedFraction(25), 0.25, 0.001);
        }
    }
}
