import re
from pathlib import Path

AVATAR = Path(__file__).resolve().parents[3]
REMOTE_SEAT_UNIT = (
    AVATAR / "home-manager/avatar-remote-seat-home-manager.nix"
).read_text()
MAC_COMMANDS = (AVATAR / "avatar-remote-home-manager.nix").read_text()
PROGRAMS = (AVATAR / "avatar-programs.nix").read_text()
UNITS = (AVATAR / "avatar-home-manager.nix").read_text()
REBUILD = (AVATAR / "home-manager/avatar-rebuild-home-manager.nix").read_text()


def kept_through_rebuild(kind):
    block = re.search(
        rf"systemd\.user\.{kind} = keepRunningThroughRebuild \[(.*?)\];", REBUILD, re.S
    )
    return set(re.findall(r'"([a-z-]+)"', block.group(1)))


def defined_services():
    services = UNITS[UNITS.index("services = {") :]
    own = re.findall(r"^        (avatar-[a-z-]+) = \{", services, re.M)
    seat = re.findall(r"systemd\.user\.services\.(avatar-[a-z-]+) =", REMOTE_SEAT_UNIT)
    return set(own) | set(seat)


def test_every_avatar_service_keeps_its_running_version_through_a_rebuild():
    assert kept_through_rebuild("services") == defined_services()


def test_every_avatar_target_keeps_running_through_a_rebuild():
    targets = set(re.findall(r"targets\.(avatar[a-z-]*)\.Unit", UNITS))
    assert kept_through_rebuild("targets") == targets


def test_a_rebuild_keeps_the_old_version_instead_of_restarting_it():
    assert 'Unit.X-SwitchMethod = "keep-old"' in REBUILD


def wrapper(source, name):
    match = re.search(
        rf'{name} = pkgs\.writeShellScriptBin "[^"]+" \'\'(.*?)\'\';', source, re.S
    )
    return match.group(1)


def test_a_seat_that_ends_stops_the_conversation_and_the_listener():
    stop = re.search(r'ExecStopPost = "(.*?)";', REMOTE_SEAT_UNIT).group(1)
    assert stop.endswith("stop avatar-conversation.target avatar-listener.service")
    assert "--no-block" in stop


def test_a_mac_gets_the_same_four_commands_as_chise():
    packages = MAC_COMMANDS[MAC_COMMANDS.index("home.packages") :]
    assert 'forwardToChise "avatar-audio"' in packages
    for verb, command in [
        ("start", "avatar-start"),
        ("stop", "avatar-stop"),
        ("listen", "avatar-listen"),
    ]:
        assert f'remoteMeeting "{verb}" "{command}"' in packages


def test_the_mac_meeting_commands_run_the_stdlib_module_with_the_caller_arguments():
    command = re.search(r"remoteMeeting =(.*?)\n  talk =", MAC_COMMANDS, re.S).group(1)
    assert "${pkgs.python312}/bin/python3" in command
    assert "remote_seat}/remote_meeting.py ${verb}" in command
    assert command.rstrip().endswith("'';")
    assert '"$@"' in command


def test_the_start_command_reaches_the_seat_modules_and_passes_its_arguments():
    start = wrapper(PROGRAMS, "start")
    assert "./scripts/conversation}" in start
    assert "./scripts/listening}" in start
    assert '${./scripts/start.py} "$@"' in start


def test_the_listen_command_reaches_the_seat_module():
    listen = wrapper(PROGRAMS, "listen")
    assert "./scripts/conversation}" in listen


def test_the_seat_outlives_a_conversation_so_a_meeting_keeps_it():
    assert "PartOf" not in REMOTE_SEAT_UNIT


def test_stopping_the_avatar_releases_the_seat():
    stop = (AVATAR / "scripts/avatar-stop").read_text()
    assert "avatar-remote-seat.service" in stop
