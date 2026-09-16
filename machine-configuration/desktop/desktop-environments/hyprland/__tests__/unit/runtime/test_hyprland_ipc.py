import hyprland_ipc


class TestGetActiveWorkspaceIdViaActiveworkspace:
    def test_returns_id_reported_by_activeworkspace(self, hyprctl_response_builder):
        hyprctl_response_builder("activeworkspace", {"id": 4})

        assert hyprland_ipc.get_active_workspace_id_via_activeworkspace() == 4

    def test_returns_none_when_activeworkspace_answers_nothing(
        self, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", None)

        assert hyprland_ipc.get_active_workspace_id_via_activeworkspace() is None

    def test_returns_none_when_activeworkspace_carries_no_id(
        self, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", {"name": "special:magic"})

        assert hyprland_ipc.get_active_workspace_id_via_activeworkspace() is None

    def test_stays_independent_from_the_active_window_workspace(
        self, hyprctl_response_builder
    ):
        hyprctl_response_builder("activeworkspace", {"id": 4})
        hyprctl_response_builder("activewindow", {"workspace": {"id": 9}})

        assert hyprland_ipc.get_active_workspace_id_via_activeworkspace() == 4
        assert hyprland_ipc.get_active_workspace_id() == 9
