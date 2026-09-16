import QtQuick
import QtTest

RunningApplicationsFixture {
    id: root

    TestCase {
        name: "RunningAppsModuleResolveIconName"

        function test_maps_chrome_global_to_google_chrome() {
            compare(runningAppsModule.resolveIconName("chrome-global"), "google-chrome");
        }

        function test_maps_code_to_vscode() {
            compare(runningAppsModule.resolveIconName("code"), "vscode");
        }

        function test_maps_code_insiders_to_vscode_insiders() {
            compare(runningAppsModule.resolveIconName("Code - Insiders"), "vscode-insiders");
        }

        function test_maps_cursor_to_cursor() {
            compare(runningAppsModule.resolveIconName("Cursor"), "cursor");
        }

        function test_unmapped_class_returns_lowercase() {
            compare(runningAppsModule.resolveIconName("Firefox"), "firefox");
        }

        function test_already_lowercase_unmapped_passes_through() {
            compare(runningAppsModule.resolveIconName("kitty"), "kitty");
        }

        function test_empty_string_returns_empty() {
            compare(runningAppsModule.resolveIconName(""), "");
        }
    }
}
