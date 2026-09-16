import importlib.util
import pathlib

LAUNCHER_SCRIPT_PATH = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts"
    / "launch_herdr_screensaver.py"
)


def _load_launcher_module():
    module_spec = importlib.util.spec_from_file_location(
        "launch_herdr_screensaver", LAUNCHER_SCRIPT_PATH
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


launcher = _load_launcher_module()


def which_returning(available_executables):
    available = set(available_executables)

    def fake_which(executable):
        return f"/usr/bin/{executable}" if executable in available else None

    return fake_which
