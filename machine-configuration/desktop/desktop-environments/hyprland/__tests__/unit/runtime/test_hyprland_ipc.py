import hyprland_ipc


class TestGetActiveWorkspaceIdViaActiveworkspace:
    def test_stays_independent_from_the_active_window_workspace(
        self, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", {"id": 4})
        hyprctl_response_builder("activewindow", {"workspace": {"id": 9}})

        assert hyprland_ipc.get_active_workspace_id_via_activeworkspace() == 4
        assert hyprland_ipc.get_active_workspace_id() == 9
