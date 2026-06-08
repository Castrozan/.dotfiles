import importlib.util
import pathlib
import sys


def load_service_module():
    service_directory = (
        pathlib.Path(__file__).resolve().parent.parent.parent / "clawde-service"
    )
    sys.path.insert(0, str(service_directory))
    module_path = service_directory / "clawde-service.py"
    module_spec = importlib.util.spec_from_file_location("clawde_service", module_path)
    module = importlib.util.module_from_spec(module_spec)
    sys.modules["clawde_service"] = module
    module_spec.loader.exec_module(module)
    return module


class FakeCompletedProcess:
    def __init__(self, returncode, stdout=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = ""


def fake_tmux_with_window_inventory(live_session_names, windows_by_session):
    def fake_run_tmux_command(*arguments):
        subcommand = arguments[0]
        if subcommand == "has-session":
            return FakeCompletedProcess(0 if arguments[2] in live_session_names else 1)
        if subcommand == "new-session":
            session_name = arguments[3]
            live_session_names.add(session_name)
            windows_by_session.setdefault(session_name, set()).add(arguments[5])
            return FakeCompletedProcess(0)
        if subcommand == "list-windows":
            return FakeCompletedProcess(
                0, stdout="\n".join(windows_by_session.get(arguments[2], set()))
            )
        if subcommand == "new-window":
            windows_by_session.setdefault(arguments[2], set()).add(arguments[4])
            return FakeCompletedProcess(0)
        return FakeCompletedProcess(0)

    return fake_run_tmux_command
