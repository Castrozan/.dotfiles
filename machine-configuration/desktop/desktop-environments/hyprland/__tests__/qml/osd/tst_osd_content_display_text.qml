import QtQuick
import QtTest

OnScreenDisplayFixture {
    id: root

    TestCase {
        name: "OsdContentDisplayText"

        function test_shows_percentage_when_not_muted() {
            compare(osdContent.computeDisplayText(false, 75), "75%");
        }

        function test_shows_m_when_muted() {
            compare(osdContent.computeDisplayText(true, 75), "M");
        }

        function test_shows_zero_percent() {
            compare(osdContent.computeDisplayText(false, 0), "0%");
        }

        function test_shows_100_percent() {
            compare(osdContent.computeDisplayText(false, 100), "100%");
        }
    }
}
