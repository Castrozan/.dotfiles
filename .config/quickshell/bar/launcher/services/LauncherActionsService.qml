pragma Singleton

import Quickshell
import QtQuick

Singleton {
    id: launcherActionsServiceRoot

    readonly property list<var> allActions: [
        {
            name: "Scheme",
            description: "Browse and switch color schemes",
            icon: "palette",
            autoCompleteText: ">scheme "
        },
        {
            name: "Wallpaper",
            description: "Browse and set wallpapers",
            icon: "wallpaper",
            autoCompleteText: ">wallpaper "
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

    function search(queryText: string): list<var> {
        let lowerQuery = queryText.toLowerCase();
        return allActions.filter(action => action.name.toLowerCase().includes(lowerQuery) || action.description.toLowerCase().includes(lowerQuery));
    }
}
