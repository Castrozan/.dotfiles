import subprocess


def process_info_for(process_identifier: int) -> tuple[int, str] | None:
    parent_process = subprocess.run(
        ["ps", "-p", str(process_identifier), "-o", "ppid="],
        capture_output=True,
        text=True,
        check=False,
    )
    command_process = subprocess.run(
        ["ps", "-ww", "-p", str(process_identifier), "-o", "command="],
        capture_output=True,
        text=True,
        check=False,
    )
    if parent_process.returncode != 0 or command_process.returncode != 0:
        return None
    try:
        parent_process_identifier = int(parent_process.stdout.strip())
    except ValueError:
        return None
    return parent_process_identifier, command_process.stdout.strip()
