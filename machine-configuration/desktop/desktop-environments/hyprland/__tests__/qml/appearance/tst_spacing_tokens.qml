import QtQuick
import QtTest

AppearanceFixture {
    id: root

    TestCase {
        name: "AppearanceSpacingTokens"

        function test_all_spacing_values_are_positive() {
            verify(appearance.spacing.smaller > 0);
            verify(appearance.spacing.small > 0);
            verify(appearance.spacing.normal > 0);
            verify(appearance.spacing.large > 0);
        }

        function test_spacing_increases_monotonically() {
            verify(appearance.spacing.smaller <= appearance.spacing.small);
            verify(appearance.spacing.small <= appearance.spacing.normal);
            verify(appearance.spacing.normal <= appearance.spacing.large);
        }

        function test_spacing_exact_values() {
            compare(appearance.spacing.smaller, 4);
            compare(appearance.spacing.small, 8);
            compare(appearance.spacing.normal, 12);
            compare(appearance.spacing.large, 16);
        }
    }
}
