import json
import os
import pathlib
import shutil
import subprocess
import sys


SCRIPTS_DIRECTORY = pathlib.Path(__file__).resolve().parents[2] / "scripts"


def test_bundled_cli_selects_installed_and_running_clients(tmp_path):
    bundle_scripts = tmp_path / "scripts"
    helper_directory = bundle_scripts / "herdr_client"
    helper_directory.mkdir(parents=True)
    entry_path = SCRIPTS_DIRECTORY / "select-herdr-client.py"
    shutil.copy2(entry_path, bundle_scripts / entry_path.name)
    shutil.copy2(
        SCRIPTS_DIRECTORY / "herdr_client" / "selection.py",
        helper_directory / "selection.py",
    )

    installed_directory = tmp_path / "installed" / "bin"
    installed_directory.mkdir(parents=True)
    installed_executable = installed_directory / "herdr"
    socket_path = tmp_path / "herdr.sock"
    response = json.dumps({"running": True, "socket": str(socket_path)})
    installed_executable.write_text(
        f"#!/usr/bin/env python3\nprint({json.dumps(response)})\n"
    )
    installed_executable.chmod(0o755)

    running_directory = tmp_path / "running" / "bin"
    running_directory.mkdir(parents=True)
    running_executable = running_directory / "herdr"
    running_executable.write_text("")
    running_executable.chmod(0o755)

    fake_binary_directory = tmp_path / "fake-bin"
    fake_binary_directory.mkdir()
    fake_lsof = fake_binary_directory / "lsof"
    fake_lsof.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        "if '-t' in sys.argv:\n"
        "    print('4242')\n"
        "else:\n"
        f"    print('p4242\\nn{running_executable}\\n')\n"
    )
    fake_lsof.chmod(0o755)
    environment = dict(os.environ)
    environment["PATH"] = f"{fake_binary_directory}{os.pathsep}{environment['PATH']}"
    bundled_entry = bundle_scripts / entry_path.name

    local_result = subprocess.run(
        [
            sys.executable,
            str(bundled_entry),
            "select",
            str(installed_executable),
            "status",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )
    running_result = subprocess.run(
        [
            sys.executable,
            str(bundled_entry),
            "select",
            str(installed_executable),
            "agent",
            "exit",
        ],
        capture_output=True,
        text=True,
        check=True,
        env=environment,
    )

    assert local_result.stdout.strip() == str(installed_executable)
    assert running_result.stdout.strip() == str(running_executable)
