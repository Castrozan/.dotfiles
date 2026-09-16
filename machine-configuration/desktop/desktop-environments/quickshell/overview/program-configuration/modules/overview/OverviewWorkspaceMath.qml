pragma Singleton
import Quickshell

Singleton {
    function workspaceRow(workspaceId, layout) {
        if (!Number.isFinite(workspaceId))
            return 0;

        const adjusted = workspaceId - layout.workspaceOffset;
        const normalRow = Math.floor((adjusted - 1) / layout.columns) % layout.rows;
        return layout.orderBottomUp ? (layout.rows - normalRow - 1) : normalRow;
    }

    function workspaceColumn(workspaceId, layout) {
        if (!Number.isFinite(workspaceId))
            return 0;

        const adjusted = workspaceId - layout.workspaceOffset;
        const normalColumn = (adjusted - 1) % layout.columns;
        return layout.orderRightLeft ? (layout.columns - normalColumn - 1) : normalColumn;
    }

    function workspaceInCell(rowIndex, columnIndex, layout) {
        const workspacesShown = layout.rows * layout.columns;
        const mappedRow = layout.orderBottomUp ? (layout.rows - rowIndex - 1) : rowIndex;
        const mappedColumn = layout.orderRightLeft ? (layout.columns - columnIndex - 1) : columnIndex;
        return (layout.workspaceGroup * workspacesShown) + (mappedRow * layout.columns) + mappedColumn + 1 + layout.workspaceOffset;
    }

    function specialWorkspaceIndex(name, visibleSpecialWorkspaces) {
        return (visibleSpecialWorkspaces ?? []).indexOf(`${name ?? ""}`);
    }

    function specialWorkspaceLabel(name) {
        const raw = `${name ?? ""}`.trim();
        if (raw.length === 0)
            return "Special";
        return raw.replace(/[-_]+/g, " ");
    }

    function nextSpecialWorkspaceName(visibleSpecialWorkspaces) {
        const taken = new Set();
        for (const name of (visibleSpecialWorkspaces ?? []))
            taken.add(`${name ?? ""}`.trim().toLowerCase());

        const base = "stash";
        if (!taken.has(base))
            return base;

        let index = 2;
        while (taken.has(`${base}-${index}`))
            index += 1;

        return `${base}-${index}`;
    }
}
