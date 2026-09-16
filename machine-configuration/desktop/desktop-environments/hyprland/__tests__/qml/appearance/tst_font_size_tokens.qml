import QtQuick
import QtTest

AppearanceFixture {
    id: root

    TestCase {
        name: "AppearanceFontSizeTokens"

        function test_all_sizes_are_positive() {
            verify(appearance.font.size.smaller > 0);
            verify(appearance.font.size.small > 0);
            verify(appearance.font.size.normal > 0);
            verify(appearance.font.size.large > 0);
            verify(appearance.font.size.larger > 0);
            verify(appearance.font.size.extraLarge > 0);
        }

        function test_sizes_increase_monotonically() {
            verify(appearance.font.size.smaller <= appearance.font.size.small);
            verify(appearance.font.size.small <= appearance.font.size.normal);
            verify(appearance.font.size.normal <= appearance.font.size.large);
            verify(appearance.font.size.large <= appearance.font.size.larger);
            verify(appearance.font.size.larger <= appearance.font.size.extraLarge);
        }

        function test_sizes_are_reasonable_pt_values() {
            verify(appearance.font.size.smaller >= 6);
            verify(appearance.font.size.extraLarge <= 72);
        }

        function test_exact_size_values() {
            compare(appearance.font.size.smaller, 9);
            compare(appearance.font.size.small, 10);
            compare(appearance.font.size.normal, 12);
            compare(appearance.font.size.large, 14);
            compare(appearance.font.size.larger, 16);
            compare(appearance.font.size.extraLarge, 20);
        }
    }
}
