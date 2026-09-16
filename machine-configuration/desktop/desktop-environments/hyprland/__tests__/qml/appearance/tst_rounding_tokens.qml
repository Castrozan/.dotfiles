import QtQuick
import QtTest

AppearanceFixture {
    id: root

    TestCase {
        name: "AppearanceRoundingTokens"

        function test_all_rounding_values_are_positive() {
            verify(appearance.rounding.small > 0);
            verify(appearance.rounding.normal > 0);
            verify(appearance.rounding.large > 0);
            verify(appearance.rounding.full > 0);
        }

        function test_rounding_increases_monotonically() {
            verify(appearance.rounding.small <= appearance.rounding.normal);
            verify(appearance.rounding.normal <= appearance.rounding.large);
            verify(appearance.rounding.large <= appearance.rounding.full);
        }

        function test_full_rounding_is_large_value() {
            verify(appearance.rounding.full >= 100);
        }

        function test_scale_is_positive() {
            verify(appearance.rounding.scale > 0);
        }

        function test_rounding_exact_values() {
            compare(appearance.rounding.small, 8);
            compare(appearance.rounding.normal, 12);
            compare(appearance.rounding.large, 16);
            compare(appearance.rounding.full, 999);
            fuzzyCompare(appearance.rounding.scale, 1.0, 0.001);
        }
    }
}
