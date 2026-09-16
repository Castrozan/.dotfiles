import QtQuick
import QtTest

AppearanceFixture {
    id: root

    TestCase {
        name: "AppearanceFontFamilyTokens"

        function test_sans_family_is_nonempty() {
            verify(appearance.font.family.sans.length > 0);
        }

        function test_material_family_is_nonempty() {
            verify(appearance.font.family.material.length > 0);
        }

        function test_clock_family_is_nonempty() {
            verify(appearance.font.family.clock.length > 0);
        }

        function test_sans_family_exact_value() {
            compare(appearance.font.family.sans, "JetBrainsMono Nerd Font");
        }

        function test_material_family_exact_value() {
            compare(appearance.font.family.material, "Material Symbols Rounded");
        }
    }
}
