from dataclasses import dataclass


@dataclass(frozen=True)
class DisplayRectangle:
    left: float
    top: float
    right: float
    bottom: float

    def intersection(self, other):
        intersection = DisplayRectangle(
            max(self.left, other.left),
            max(self.top, other.top),
            min(self.right, other.right),
            min(self.bottom, other.bottom),
        )
        if intersection.right <= intersection.left:
            return None
        if intersection.bottom <= intersection.top:
            return None
        return intersection

    def contains(self, other):
        return (
            self.left <= other.left
            and self.top <= other.top
            and self.right >= other.right
            and self.bottom >= other.bottom
        )


def window_rectangle(window):
    left, top = window["at"]
    width, height = window["size"]
    return DisplayRectangle(left, top, left + width, top + height)


def monitor_rectangle(monitor):
    width, height = monitor["width"], monitor["height"]
    if monitor.get("transform", 0) in (1, 3, 5, 7):
        width, height = height, width
    scale = monitor["scale"]
    if scale <= 0:
        raise ValueError("Monitor scale must be positive")
    return DisplayRectangle(
        monitor["x"],
        monitor["y"],
        monitor["x"] + width / scale,
        monitor["y"] + height / scale,
    )


def window_is_mapped(window):
    return window.get("mapped", False) and not window.get("hidden", True)


def find_player_window(clients, player_process_id):
    return next(
        (client for client in clients if client.get("pid") == player_process_id), None
    )


def player_is_mapped_on_workspace(player, target_workspace_id):
    if not window_is_mapped(player):
        return False
    return player["workspace"]["id"] == target_workspace_id


def monitor_is_displaying_workspace(monitor, target_workspace_id):
    if monitor.get("disabled", False):
        return False
    if not monitor.get("dpmsStatus", True):
        return False
    return monitor["activeWorkspace"]["id"] == target_workspace_id


def client_is_fullscreen_on_workspaces(client, workspace_ids):
    if not window_is_mapped(client):
        return False
    if client.get("fullscreen", 0) == 0:
        return False
    return client["workspace"]["id"] in workspace_ids


def visible_rectangle_is_covered(
    clients, player_process_id, workspace_ids, visible_rectangle
):
    return any(
        client.get("pid") != player_process_id
        and client_is_fullscreen_on_workspaces(client, workspace_ids)
        and window_rectangle(client).contains(visible_rectangle)
        for client in clients
    )


def monitor_shows_uncovered_rectangle(
    monitor, clients, player_rectangle, player_process_id, target_workspace_id
):
    if not monitor_is_displaying_workspace(monitor, target_workspace_id):
        return False
    visible_rectangle = player_rectangle.intersection(monitor_rectangle(monitor))
    if visible_rectangle is None:
        return False
    workspace_ids = {
        target_workspace_id,
        monitor.get("specialWorkspace", {}).get("id", 0),
    }
    return not visible_rectangle_is_covered(
        clients, player_process_id, workspace_ids, visible_rectangle
    )


def released_player_would_be_visible(
    clients, monitors, player_process_id, target_workspace_id
):
    return any(
        monitor_shows_uncovered_rectangle(
            monitor,
            clients,
            monitor_rectangle(monitor),
            player_process_id,
            target_workspace_id,
        )
        for monitor in monitors
    )


def player_is_visible(clients, monitors, player_process_id, target_workspace_id):
    player = find_player_window(clients, player_process_id)
    if player is None:
        return released_player_would_be_visible(
            clients, monitors, player_process_id, target_workspace_id
        )
    if not player_is_mapped_on_workspace(player, target_workspace_id):
        return False
    player_rectangle = window_rectangle(player)
    return any(
        monitor_shows_uncovered_rectangle(
            monitor, clients, player_rectangle, player_process_id, target_workspace_id
        )
        for monitor in monitors
    )
