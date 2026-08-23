from unittest.mock import MagicMock, patch

import hyprland_runtime


def completed_process(returncode: int) -> MagicMock:
    result = MagicMock()
    result.returncode = returncode
    return result


class TestIsHyprctlConnected:
    def test_returns_true_when_hyprctl_succeeds(self):
        with patch(
            "hyprland_runtime.subprocess.run",
            return_value=completed_process(0),
        ) as mock_run:
            assert hyprland_runtime.is_hyprctl_connected() is True
            mock_run.assert_called_once_with(
                ["hyprctl", "monitors"],
                capture_output=True,
                text=True,
            )

    def test_returns_false_when_hyprctl_fails(self):
        with patch(
            "hyprland_runtime.subprocess.run",
            return_value=completed_process(1),
        ):
            assert hyprland_runtime.is_hyprctl_connected() is False


class TestFindLiveHyprlandSocket:
    def test_returns_false_when_runtime_directory_is_missing(self, tmp_path):
        with patch("hyprland_runtime.os.getuid", return_value=1000):
            with patch("hyprland_runtime.Path", return_value=tmp_path / "hypr"):
                assert hyprland_runtime.find_live_hyprland_socket() is False

    def test_returns_false_when_no_signature_answers(self, tmp_path):
        hypr_dir = tmp_path / "hypr"
        (hypr_dir / "dead").mkdir(parents=True)

        with patch("hyprland_runtime.os.getuid", return_value=1000):
            with patch("hyprland_runtime.Path", return_value=hypr_dir):
                with patch(
                    "hyprland_runtime.subprocess.run",
                    return_value=completed_process(1),
                ):
                    assert hyprland_runtime.find_live_hyprland_socket() is False

    def test_exports_the_signature_that_answers(self, tmp_path):
        hypr_dir = tmp_path / "hypr"
        (hypr_dir / "dead").mkdir(parents=True)
        (hypr_dir / "live").mkdir()
        (hypr_dir / "stray-file").write_text("")

        def answer_only_for_live_signature(_command, **kwargs):
            signature = kwargs["env"]["HYPRLAND_INSTANCE_SIGNATURE"]
            return completed_process(0 if signature == "live" else 1)

        with patch("hyprland_runtime.os.getuid", return_value=1000):
            with patch("hyprland_runtime.Path", return_value=hypr_dir):
                with patch.dict(hyprland_runtime.os.environ):
                    with patch(
                        "hyprland_runtime.subprocess.run",
                        side_effect=answer_only_for_live_signature,
                    ):
                        assert hyprland_runtime.find_live_hyprland_socket() is True
                        assert (
                            hyprland_runtime.os.environ["HYPRLAND_INSTANCE_SIGNATURE"]
                            == "live"
                        )


class TestEnsureHyprctlConnected:
    def test_returns_true_without_searching_when_already_connected(self):
        with patch("hyprland_runtime.is_hyprctl_connected", return_value=True):
            with patch("hyprland_runtime.find_live_hyprland_socket") as mock_search:
                assert hyprland_runtime.ensure_hyprctl_connected() is True
                mock_search.assert_not_called()

    def test_falls_back_to_socket_search_when_not_connected(self):
        with patch("hyprland_runtime.is_hyprctl_connected", return_value=False):
            with patch(
                "hyprland_runtime.find_live_hyprland_socket",
                return_value=True,
            ):
                assert hyprland_runtime.ensure_hyprctl_connected() is True

    def test_returns_false_when_no_socket_answers(self):
        with patch("hyprland_runtime.is_hyprctl_connected", return_value=False):
            with patch(
                "hyprland_runtime.find_live_hyprland_socket",
                return_value=False,
            ):
                assert hyprland_runtime.ensure_hyprctl_connected() is False
