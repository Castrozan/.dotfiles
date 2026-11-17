import re
from pathlib import Path

AVATAR = Path(__file__).resolve().parents[3]
REMOTE_SEAT_UNIT = (
    AVATAR / "home-manager/avatar-remote-seat-home-manager.nix"
).read_text()
MAC_COMMANDS = (AVATAR / "avatar-remote-home-manager.nix").read_text()
MAC_CONVERSATION = (AVATAR / "home-manager/avatar-mac-conversation.nix").read_text()
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


def test_a_mac_gets_the_same_four_commands_as_chise_and_forwards_none_to_it():
    packages = MAC_COMMANDS[MAC_COMMANDS.index("home.packages") :]
    assert "forwardToHost" not in MAC_COMMANDS
    for command in ["avatar-start", "avatar-stop", "avatar-controls", "avatar-listen"]:
        assert f'conversation.meetingCommand "{command}"' in packages


def test_the_floor_command_is_defined_once_and_the_mac_talk_command_uses_it():
    assert "avatar-claim-floor" not in MAC_CONVERSATION
    assert "        programs.floor\n" in MAC_CONVERSATION


def test_the_mac_meeting_commands_run_the_local_modules_with_the_caller_arguments():
    command = MAC_CONVERSATION.split("meetingCommand =")[1].split("listener =")[0]
    assert "${conversationPython}/bin/python3" in command
    assert "/conversation/mac_conversation/${entry}" in command
    assert "${environment}" in command
    assert "programs.unclaimedCommand" in command
    assert command.rstrip().endswith("'';")
    assert '"$@"' in command


def test_the_start_command_reaches_the_seat_modules_and_passes_its_arguments():
    start = wrapper(PROGRAMS, "start")
    assert "./scripts/conversation}" in start
    assert "./scripts/listening}" in start
    assert '${./scripts/meetings/start.py} "$@"' in start


def test_the_listen_command_reaches_the_seat_module():
    listen = wrapper(PROGRAMS, "listen")
    assert "./scripts/conversation}" in listen


def test_the_seat_outlives_a_conversation_so_a_meeting_keeps_it():
    assert "PartOf" not in REMOTE_SEAT_UNIT


def test_stopping_the_avatar_releases_the_seat():
    stop = (AVATAR / "scripts/avatar-stop").read_text()
    assert "avatar-remote-seat.service" in stop


def test_the_wake_on_chise_comes_back_whenever_it_ends():
    chise_wake = (AVATAR / "avatar-wake-home-manager.nix").read_text()
    assert 'Restart = "always";' in chise_wake


def test_the_avatar_host_is_named_once_and_every_mac_command_reads_it():
    topology = (AVATAR / "home-manager/avatar-topology.nix").read_text()
    assert re.findall(r'host = "([a-z]+)";', topology) == ["chise"]
    assert "chise" not in MAC_COMMANDS
    assert MAC_COMMANDS.count("export AVATAR_HOST=${topology.host}") == 1
    assert "inherit (topology) host;" in MAC_COMMANDS
    assert "export AVATAR_HOST=${host}" in MAC_CONVERSATION


def test_every_machine_gets_the_doctor():
    assert "import ./home-manager/avatar-doctor-package.nix" in MAC_COMMANDS
    assert 'arguments = "--seat-of ${topology.host}";' in MAC_COMMANDS
    host = (AVATAR / "home-manager/avatar-doctor-home-manager.nix").read_text()
    assert "./home-manager/avatar-doctor-home-manager.nix" in UNITS
    assert "import ./avatar-doctor-package.nix" in host
    assert 'arguments = "";' in host


def test_the_linux_talk_command_knows_the_name_of_its_machine():
    talk = wrapper(PROGRAMS, "talk")
    assert (
        '${lib.optionalString (hostname != null) "export AVATAR_AGENT_HOST=${hostname}"}'
        in talk
    )
    assert "hostname ? null," in PROGRAMS


def test_the_linux_module_that_installs_talk_passes_the_hostname():
    assert "isNixOS,\n  hostname,\n" in UNITS
    assert "inherit pkgs lib inputs;\n    inherit hostname;" in UNITS
