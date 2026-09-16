import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: coloursLogic

        function layer(baseColor, level) {
            return Qt.lighter(baseColor, 1 + level * 0.05);
        }
    }

    TestCase {
        name: "ColoursLayerFunction"

        function test_level_zero_returns_same_color() {
            var base = Qt.rgba(0.5, 0.5, 0.5, 1.0);
            var result = coloursLogic.layer(base, 0);
            fuzzyCompare(result.r, base.r, 0.01);
            fuzzyCompare(result.g, base.g, 0.01);
            fuzzyCompare(result.b, base.b, 0.01);
        }

        function test_level_one_lightens_by_five_percent() {
            var base = Qt.rgba(0.5, 0.5, 0.5, 1.0);
            var result = coloursLogic.layer(base, 1);
            var expected = Qt.lighter(base, 1.05);
            fuzzyCompare(result.r, expected.r, 0.01);
            fuzzyCompare(result.g, expected.g, 0.01);
            fuzzyCompare(result.b, expected.b, 0.01);
        }

        function test_level_two_lightens_by_ten_percent() {
            var base = Qt.rgba(0.5, 0.5, 0.5, 1.0);
            var result = coloursLogic.layer(base, 2);
            var expected = Qt.lighter(base, 1.10);
            fuzzyCompare(result.r, expected.r, 0.01);
            fuzzyCompare(result.g, expected.g, 0.01);
            fuzzyCompare(result.b, expected.b, 0.01);
        }

        function test_higher_level_produces_lighter_color() {
            var base = Qt.rgba(0.3, 0.3, 0.3, 1.0);
            var level1 = coloursLogic.layer(base, 1);
            var level3 = coloursLogic.layer(base, 3);
            verify(level3.r > level1.r);
            verify(level3.g > level1.g);
            verify(level3.b > level1.b);
        }

        function test_preserves_alpha() {
            var base = Qt.rgba(0.5, 0.5, 0.5, 0.7);
            var result = coloursLogic.layer(base, 2);
            fuzzyCompare(result.a, 0.7, 0.01);
        }

        function test_black_base_at_level_zero() {
            var base = Qt.rgba(0, 0, 0, 1.0);
            var result = coloursLogic.layer(base, 0);
            fuzzyCompare(result.r, 0, 0.01);
            fuzzyCompare(result.g, 0, 0.01);
            fuzzyCompare(result.b, 0, 0.01);
        }

        function test_white_base_stays_white_or_lighter() {
            var base = Qt.rgba(1.0, 1.0, 1.0, 1.0);
            var result = coloursLogic.layer(base, 1);
            verify(result.r >= 1.0 - 0.01);
            verify(result.g >= 1.0 - 0.01);
            verify(result.b >= 1.0 - 0.01);
        }

        function test_named_color_as_base() {
            var result = coloursLogic.layer("red", 1);
            var expected = Qt.lighter("red", 1.05);
            fuzzyCompare(result.r, expected.r, 0.01);
            fuzzyCompare(result.g, expected.g, 0.01);
            fuzzyCompare(result.b, expected.b, 0.01);
        }

        function test_hex_color_as_base() {
            var result = coloursLogic.layer("#1e1e2e", 2);
            var expected = Qt.lighter("#1e1e2e", 1.10);
            fuzzyCompare(result.r, expected.r, 0.01);
            fuzzyCompare(result.g, expected.g, 0.01);
            fuzzyCompare(result.b, expected.b, 0.01);
        }

        function test_large_level_value() {
            var base = Qt.rgba(0.5, 0.5, 0.5, 1.0);
            var result = coloursLogic.layer(base, 10);
            var expected = Qt.lighter(base, 1.50);
            fuzzyCompare(result.r, expected.r, 0.01);
            fuzzyCompare(result.g, expected.g, 0.01);
        }
    }
}
