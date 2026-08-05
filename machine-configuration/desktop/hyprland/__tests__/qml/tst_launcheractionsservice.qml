import QtQuick
import QtTest

Item {
    id: root

    readonly property var allActions: [
        {
            name: "Wallpaper",
            description: "Browse and set wallpapers",
            icon: "wallpaper",
            autoCompleteText: ":wallpaper "
        },
        {
            name: "Next Wallpaper",
            description: "Switch to next wallpaper",
            icon: "skip_next",
            command: "hypr-theme-bg-next"
        },
        {
            name: "Lock",
            description: "Lock the screen",
            icon: "lock",
            command: "hyprlock"
        },
        {
            name: "Reboot",
            description: "Restart the computer",
            icon: "restart_alt",
            command: "systemctl reboot"
        },
        {
            name: "Shutdown",
            description: "Power off the computer",
            icon: "power_settings_new",
            command: "systemctl poweroff"
        }
    ]

    QtObject {
        id: launcherActionsService

        function search(queryText) {
            var lowerQuery = queryText.toLowerCase();
            return root.allActions.filter(function(action) {
                return action.name.toLowerCase().includes(lowerQuery) || action.description.toLowerCase().includes(lowerQuery);
            });
        }
    }

    TestCase {
        name: "LauncherActionsServiceSearch"

        function test_search_matches_by_action_name() {
            var results = launcherActionsService.search("lock");
            compare(results.length, 1);
            compare(results[0].name, "Lock");
        }

        function test_search_matches_by_description() {
            var results = launcherActionsService.search("power off");
            compare(results.length, 1);
            compare(results[0].name, "Shutdown");
        }

        function test_search_is_case_insensitive() {
            var results = launcherActionsService.search("REBOOT");
            compare(results.length, 1);
            compare(results[0].name, "Reboot");
        }

        function test_search_returns_multiple_matches() {
            var results = launcherActionsService.search("wallpaper");
            compare(results.length, 2);
        }

        function test_search_returns_empty_for_no_match() {
            var results = launcherActionsService.search("zzzznonexistent");
            compare(results.length, 0);
        }

        function test_search_empty_query_returns_all() {
            var results = launcherActionsService.search("");
            compare(results.length, 5);
        }

        function test_search_partial_name_match() {
            var results = launcherActionsService.search("reb");
            compare(results.length, 1);
            compare(results[0].name, "Reboot");
        }

        function test_search_partial_description_match() {
            var results = launcherActionsService.search("restart the");
            compare(results.length, 1);
            compare(results[0].name, "Reboot");
        }

        function test_search_matches_description_across_actions() {
            var results = launcherActionsService.search("the");
            verify(results.length >= 3);
        }

        function test_wallpaper_action_has_autocomplete_text() {
            var results = launcherActionsService.search("wallpaper");
            var wallpaperAction = null;
            for (var i = 0; i < results.length; i++) {
                if (results[i].name === "Wallpaper") {
                    wallpaperAction = results[i];
                    break;
                }
            }
            verify(wallpaperAction !== null);
            compare(wallpaperAction.autoCompleteText, ":wallpaper ");
        }

        function test_non_wallpaper_actions_have_commands() {
            var results = launcherActionsService.search("lock");
            compare(results[0].command, "hyprlock");
        }
    }

    TestCase {
        name: "LauncherActionsServiceDataIntegrity"

        function test_all_actions_have_required_fields() {
            for (var i = 0; i < root.allActions.length; i++) {
                var action = root.allActions[i];
                verify(action.name !== undefined && action.name.length > 0,
                    "Action at index " + i + " missing name");
                verify(action.description !== undefined && action.description.length > 0,
                    "Action at index " + i + " missing description");
                verify(action.icon !== undefined && action.icon.length > 0,
                    "Action at index " + i + " missing icon");
            }
        }

        function test_actions_have_either_command_or_autocomplete() {
            for (var i = 0; i < root.allActions.length; i++) {
                var action = root.allActions[i];
                var hasCommand = action.command !== undefined && action.command.length > 0;
                var hasAutoComplete = action.autoCompleteText !== undefined && action.autoCompleteText.length > 0;
                verify(hasCommand || hasAutoComplete,
                    "Action '" + action.name + "' has neither command nor autoCompleteText");
            }
        }

        function test_total_action_count() {
            compare(root.allActions.length, 5);
        }
    }
}
