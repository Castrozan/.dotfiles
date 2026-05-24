import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: timeServiceLogic

        property string timeStr: ""

        readonly property var timeComponents: timeStr.split(":")
        readonly property string hourStr: timeComponents[0] ?? ""
        readonly property string minuteStr: timeComponents[1] ?? ""
        readonly property string amPmStr: timeComponents[2] ?? ""

        function formatDateTimeFromDate(dateValue, formatString) {
            return Qt.formatDateTime(dateValue, formatString);
        }
    }

    TestCase {
        name: "TimeServiceTimeComponents"

        function test_twenty_four_hour_format() {
            timeServiceLogic.timeStr = "14:30";
            compare(timeServiceLogic.hourStr, "14");
            compare(timeServiceLogic.minuteStr, "30");
            compare(timeServiceLogic.amPmStr, "");
        }

        function test_twelve_hour_format_with_am_pm() {
            timeServiceLogic.timeStr = "02:30:PM";
            compare(timeServiceLogic.hourStr, "02");
            compare(timeServiceLogic.minuteStr, "30");
            compare(timeServiceLogic.amPmStr, "PM");
        }

        function test_twelve_hour_am() {
            timeServiceLogic.timeStr = "12:00:AM";
            compare(timeServiceLogic.hourStr, "12");
            compare(timeServiceLogic.minuteStr, "00");
            compare(timeServiceLogic.amPmStr, "AM");
        }

        function test_midnight_twenty_four_hour() {
            timeServiceLogic.timeStr = "00:00";
            compare(timeServiceLogic.hourStr, "00");
            compare(timeServiceLogic.minuteStr, "00");
            compare(timeServiceLogic.amPmStr, "");
        }

        function test_empty_time_string() {
            timeServiceLogic.timeStr = "";
            compare(timeServiceLogic.hourStr, "");
            compare(timeServiceLogic.minuteStr, "");
            compare(timeServiceLogic.amPmStr, "");
        }

        function test_end_of_day() {
            timeServiceLogic.timeStr = "23:59";
            compare(timeServiceLogic.hourStr, "23");
            compare(timeServiceLogic.minuteStr, "59");
        }
    }

    TestCase {
        name: "TimeServiceFormatDateTime"

        function test_formats_date_with_hour_minute() {
            var testDate = new Date(2026, 2, 29, 14, 30, 0);
            var result = timeServiceLogic.formatDateTimeFromDate(testDate, "hh:mm");
            compare(result, "14:30");
        }

        function test_formats_date_with_twelve_hour_clock() {
            var testDate = new Date(2026, 2, 29, 14, 30, 0);
            var result = timeServiceLogic.formatDateTimeFromDate(testDate, "hh:mm:A");
            verify(result.indexOf("PM") !== -1 || result.indexOf("pm") !== -1);
        }

        function test_formats_morning_time() {
            var testDate = new Date(2026, 2, 29, 9, 5, 0);
            var result = timeServiceLogic.formatDateTimeFromDate(testDate, "hh:mm");
            compare(result, "09:05");
        }

        function test_formats_midnight() {
            var testDate = new Date(2026, 2, 29, 0, 0, 0);
            var result = timeServiceLogic.formatDateTimeFromDate(testDate, "hh:mm");
            compare(result, "00:00");
        }

        function test_formats_date_string() {
            var testDate = new Date(2026, 2, 29, 0, 0, 0);
            var result = timeServiceLogic.formatDateTimeFromDate(testDate, "yyyy-MM-dd");
            compare(result, "2026-03-29");
        }

        function test_formats_day_of_week() {
            var testDate = new Date(2026, 2, 29, 0, 0, 0);
            var result = timeServiceLogic.formatDateTimeFromDate(testDate, "ddd");
            verify(result.length > 0);
        }
    }
}
