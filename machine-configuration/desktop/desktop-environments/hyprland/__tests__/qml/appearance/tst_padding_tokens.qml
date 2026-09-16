import QtQuick
import QtTest

AppearanceFixture {
    id: root

    TestCase {
        name: "AppearancePaddingTokens"

        function test_all_padding_values_are_positive() {
            verify(appearance.padding.smaller > 0);
            verify(appearance.padding.small > 0);
            verify(appearance.padding.normal > 0);
            verify(appearance.padding.large > 0);
        }

        function test_padding_increases_monotonically() {
            verify(appearance.padding.smaller <= appearance.padding.small);
            verify(appearance.padding.small <= appearance.padding.normal);
            verify(appearance.padding.normal <= appearance.padding.large);
        }

        function test_padding_exact_values() {
            compare(appearance.padding.smaller, 4);
            compare(appearance.padding.small, 8);
            compare(appearance.padding.normal, 12);
            compare(appearance.padding.large, 16);
        }
    }
}
