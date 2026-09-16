import QtQuick
import "../../common"

QtObject {
    property var monitor
    property var windowByAddress: ({})
    property var allWorkspaces: []
    property var configuredSpecialWorkspaces: []
    property bool showSpecialWorkspaces: false
    property int columnCount: 1
    property real scale: 1
    property real workspaceSpacing: 0
    property real tileHeight: 0
    property real sectionWidth: 0
    property real workspaceGridHeight: 0

    readonly property var monitorSpecialWorkspaceNames: {
        const names = [];
        for (const workspace of (allWorkspaces ?? [])) {
            const name = `${workspace?.name ?? ""}`;
            if (!name.startsWith("special:"))
                continue;
            if (`${workspace?.monitor ?? ""}` !== `${monitor?.name ?? ""}`)
                continue;
            names.push(name.slice(8));
        }
        return names;
    }

    readonly property var windowSpecialWorkspaceNames: {
        const names = [];
        for (const address in windowByAddress) {
            const windowData = windowByAddress[address];
            if ((windowData?.monitor ?? -1) !== (monitor?.id ?? -1))
                continue;
            const workspaceName = `${windowData?.workspace?.name ?? ""}`;
            if (!workspaceName.startsWith("special:"))
                continue;
            names.push(workspaceName.slice(8));
        }
        return names;
    }

    readonly property var visibleSpecialWorkspaces: {
        if (!showSpecialWorkspaces)
            return [];

        const out = [];
        const pushUnique = (value) => {
            const cleaned = `${value ?? ""}`.trim();
            if (cleaned.length === 0 || out.includes(cleaned))
                return;
            out.push(cleaned);
        };

        for (const configured of configuredSpecialWorkspaces ?? [])
            pushUnique(configured);
        for (const name of monitorSpecialWorkspaceNames)
            pushUnique(name);
        for (const name of windowSpecialWorkspaceNames)
            pushUnique(name);

        return out;
    }

    readonly property bool hasSpecialWorkspaceSection: visibleSpecialWorkspaces.length > 0
    readonly property int tileCount: visibleSpecialWorkspaces.length + 1
    readonly property real stripGap: workspaceSpacing * 1.8
    readonly property real stripPadding: Math.max(8, 12 * scale)
    readonly property real stripTitleHeight: Math.max(14, Appearance.font.pixelSize.small * scale)
    readonly property real stripTitleGap: Math.max(6, 8 * scale)
    readonly property real tileGridInnerWidth: Math.max(0, sectionWidth - stripPadding * 2)
    readonly property int effectiveColumnCount: Math.max(1, Math.min(columnCount, tileCount))
    readonly property int tileRowCount: Math.ceil(tileCount / effectiveColumnCount)
    readonly property real tileAspectCap: {
        let maxAspect = 1;
        for (const name of visibleSpecialWorkspaces) {
            const geometry = specialWorkspaceGeometry(name);
            const width = geometry?.width;
            const height = geometry?.height;
            if (!Number.isFinite(width) || !Number.isFinite(height) || height <= 0)
                continue;
            maxAspect = Math.max(maxAspect, width / height);
        }
        return maxAspect;
    }
    readonly property real tileWidth: {
        const gaps = Math.max(0, effectiveColumnCount - 1);
        const rawWidth = (tileGridInnerWidth - gaps * workspaceSpacing) / effectiveColumnCount;
        const aspectWidth = tileHeight * tileAspectCap;
        const cappedWidth = Math.min(rawWidth, aspectWidth);
        return Math.max(80 * scale, cappedWidth);
    }
    readonly property real tileGridUsedWidth: effectiveColumnCount * tileWidth + Math.max(0, effectiveColumnCount - 1) * workspaceSpacing
    readonly property real tileGridOffsetX: stripPadding + Math.max(0, (tileGridInnerWidth - tileGridUsedWidth) / 2)
    readonly property real tileGridTop: stripPadding + stripTitleHeight + stripTitleGap
    readonly property real tileGridHeight: tileRowCount * tileHeight + Math.max(0, tileRowCount - 1) * workspaceSpacing
    readonly property real stripTop: workspaceGridHeight + workspaceSpacing + stripGap
    readonly property real stripTilesTop: stripTop + tileGridTop
    readonly property real stripHeight: stripPadding * 2 + stripTitleHeight + stripTitleGap + tileGridHeight

    function isSpecialWorkspace(windowData) {
        return `${windowData?.workspace?.name ?? ""}`.startsWith("special:");
    }

    function specialWorkspaceName(windowData) {
        const workspaceName = `${windowData?.workspace?.name ?? ""}`;
        return workspaceName.startsWith("special:") ? workspaceName.slice(8) : "";
    }

    function specialWindowZ(windowData) {
        const pinned = windowData?.pinned ? 200000 : 0;
        const floating = windowData?.floating ? 100000 : 0;
        const focus = 10000 - (windowData?.focusHistoryID ?? 9999);
        return pinned + floating + focus;
    }

    function specialWorkspaceGeometry(name) {
        const trimmedName = `${name ?? ""}`.trim();
        const currentMonitorId = monitor?.id ?? -1;
        let minX = null;
        let minY = null;
        let maxX = null;
        let maxY = null;

        for (const address in windowByAddress) {
            const windowData = windowByAddress[address];
            if ((windowData?.monitor ?? -1) !== currentMonitorId)
                continue;
            if (specialWorkspaceName(windowData) !== trimmedName)
                continue;

            const atX = windowData?.at?.[0];
            const atY = windowData?.at?.[1];
            const width = windowData?.size?.[0];
            const height = windowData?.size?.[1];
            if (!Number.isFinite(atX) || !Number.isFinite(atY))
                continue;
            if (!Number.isFinite(width) || !Number.isFinite(height))
                continue;

            minX = minX === null ? atX : Math.min(minX, atX);
            minY = minY === null ? atY : Math.min(minY, atY);
            maxX = maxX === null ? (atX + width) : Math.max(maxX, atX + width);
            maxY = maxY === null ? (atY + height) : Math.max(maxY, atY + height);
        }

        return {
            x: minX,
            y: minY,
            width: (minX !== null && maxX !== null) ? Math.max(1, maxX - minX) : null,
            height: (minY !== null && maxY !== null) ? Math.max(1, maxY - minY) : null
        };
    }
}
