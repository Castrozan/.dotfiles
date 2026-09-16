import QtQuick
import Quickshell.Hyprland
import "../../common"
import "../../services"

Item {
    id: keyboardNavigation
    required property var monitor

    Keys.onPressed: event => {
        // close: Escape or Enter
        if (event.key === Qt.Key_Escape || event.key === Qt.Key_Return) {
            GlobalStates.overviewOpen = false;
            event.accepted = true;
            return;
        }

        // Helper: compute current group bounds
        const workspacesPerGroup = Config.options.overview.rows * Config.options.overview.columns;
        const currentId = Hyprland.focusedMonitor?.activeWorkspace?.id ?? 1;
        const useWorkspaceMap = Config.options.overview.useWorkspaceMap;
        const workspaceMap = Config.options.overview.workspaceMap ?? [];
        const focusedMonitorId = Hyprland.focusedMonitor?.id ?? keyboardNavigation.monitor?.id ?? 0;
        const workspaceOffset = useWorkspaceMap ? Number(workspaceMap[focusedMonitorId] ?? 0) : 0;
        const currentGroup = Math.floor((currentId - workspaceOffset - 1) / workspacesPerGroup);
        const minWorkspaceId = currentGroup * workspacesPerGroup + 1 + workspaceOffset;
        const maxWorkspaceId = minWorkspaceId + workspacesPerGroup - 1;

        const rows = Config.options.overview.rows;
        const columns = Config.options.overview.columns;
        const reverseColumns = Config.options.overview.orderRightLeft;
        const reverseRows = Config.options.overview.orderBottomUp;

        const clampedIndex = Math.max(0, Math.min(workspacesPerGroup - 1, currentId - minWorkspaceId));
        const currentNormalRow = Math.floor(clampedIndex / columns);
        const currentNormalColumn = clampedIndex % columns;

        function toVisualRow(normalRow) {
            return reverseRows ? (rows - normalRow - 1) : normalRow;
        }

        function toVisualColumn(normalColumn) {
            return reverseColumns ? (columns - normalColumn - 1) : normalColumn;
        }

        function toNormalRow(visualRow) {
            return reverseRows ? (rows - visualRow - 1) : visualRow;
        }

        function toNormalColumn(visualColumn) {
            return reverseColumns ? (columns - visualColumn - 1) : visualColumn;
        }

        let targetVisualRow = toVisualRow(currentNormalRow);
        let targetVisualColumn = toVisualColumn(currentNormalColumn);

        let targetId = null;

        // Arrow keys and vim-style hjkl
        if (event.key === Qt.Key_Left || event.key === Qt.Key_H) {
            targetVisualColumn = (targetVisualColumn - 1 + columns) % columns;
        } else if (event.key === Qt.Key_Right || event.key === Qt.Key_L) {
            targetVisualColumn = (targetVisualColumn + 1) % columns;
        } else if (event.key === Qt.Key_Up || event.key === Qt.Key_K) {
            targetVisualRow = (targetVisualRow - 1 + rows) % rows;
        } else if (event.key === Qt.Key_Down || event.key === Qt.Key_J) {
            targetVisualRow = (targetVisualRow + 1) % rows;
        } else

        // Number keys: jump to workspace within the current group
        // 1-9 map to positions 1-9, 0 maps to position 10
        if (event.key >= Qt.Key_1 && event.key <= Qt.Key_9) {
            const position = event.key - Qt.Key_0; // 1-9
            if (position <= workspacesPerGroup) {
                targetId = minWorkspaceId + position - 1;
            }
        } else if (event.key === Qt.Key_0) {
            // 0 = 10th workspace in the group (if group has 10+ workspaces)
            if (workspacesPerGroup >= 10) {
                targetId = minWorkspaceId + 9; // 10th position = offset 9
            }
        }

        if (targetId === null && (event.key === Qt.Key_Left || event.key === Qt.Key_H || event.key === Qt.Key_Right || event.key === Qt.Key_L || event.key === Qt.Key_Up || event.key === Qt.Key_K || event.key === Qt.Key_Down || event.key === Qt.Key_J)) {
            const targetNormalRow = toNormalRow(targetVisualRow);
            const targetNormalColumn = toNormalColumn(targetVisualColumn);
            targetId = minWorkspaceId + targetNormalRow * columns + targetNormalColumn;
        }

        if (targetId !== null) {
            const clampedTarget = Math.max(minWorkspaceId, Math.min(maxWorkspaceId, targetId));
            Hyprland.dispatch("workspace " + clampedTarget);
            event.accepted = true;
        }
    }
}
