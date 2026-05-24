import ctypes
import ctypes.util
import glob
import json
import os
import socket
import subprocess
import time

SOCKET_PATH = "/tmp/workspace-switcher.sock"
ACTIVE_FLAG_PATH = "/tmp/workspace-switcher.active"
MOUSE_MOVEMENT_ITERATIONS = 20
MOUSE_MOVEMENT_PIXEL_OFFSET = 5
COMMAND_SETTLE_DELAY_SECONDS = 0.15
PERFORMANCE_THRESHOLD_SECONDS = 0.10
SOCKET_CONNECT_RETRY_ATTEMPTS = 3
SOCKET_CONNECT_RETRY_DELAY_SECONDS = 0.5

KARABINER_CORE_SERVICE_PROCESS_NAME = "Karabiner-Core-Service"

AEROSPACE_SOCKET_GLOB_PATTERN = "/tmp/bobko.aerospace-*.sock"
FOCUS_EVENT_PROPAGATION_DELAY_SECONDS = 0.25
AUTO_COMMIT_TIMEOUT_BUFFER_SECONDS = 11.0


core_graphics = ctypes.cdll.LoadLibrary(
    "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
)


class CGPoint(ctypes.Structure):
    _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]


core_graphics.CGEventCreate.restype = ctypes.c_void_p
core_graphics.CGEventCreate.argtypes = [ctypes.c_void_p]
core_graphics.CGEventGetLocation.restype = CGPoint
core_graphics.CGEventGetLocation.argtypes = [ctypes.c_void_p]
core_graphics.CGEventCreateMouseEvent.restype = ctypes.c_void_p
core_graphics.CGEventCreateMouseEvent.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint32,
    CGPoint,
    ctypes.c_uint32,
]
core_graphics.CGEventPost.restype = None
core_graphics.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
core_graphics.CFRelease.restype = None
core_graphics.CFRelease.argtypes = [ctypes.c_void_p]

CGEVENT_MOUSE_MOVED = 5
CGEVENT_TAP_HID = 0


def get_current_mouse_position():
    event = core_graphics.CGEventCreate(None)
    point = core_graphics.CGEventGetLocation(event)
    core_graphics.CFRelease(event)
    return point.x, point.y


def move_mouse_to_absolute_position(target_x, target_y):
    point = CGPoint(target_x, target_y)
    event = core_graphics.CGEventCreateMouseEvent(None, CGEVENT_MOUSE_MOVED, point, 0)
    core_graphics.CGEventPost(CGEVENT_TAP_HID, event)
    core_graphics.CFRelease(event)


def move_mouse_by_offset(delta_x, delta_y):
    current_x, current_y = get_current_mouse_position()
    move_mouse_to_absolute_position(current_x + delta_x, current_y + delta_y)


def send_command_to_daemon(command):
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    client_socket.settimeout(2)
    try:
        client_socket.sendto(command.encode(), SOCKET_PATH)
    finally:
        client_socket.close()


def is_switcher_active():
    return os.path.exists(ACTIVE_FLAG_PATH)


def measure_command_round_trip_latency(command):
    start_time = time.monotonic()
    send_command_to_daemon(command)
    elapsed_time = time.monotonic() - start_time
    return elapsed_time


def is_karabiner_core_service_running():
    result = subprocess.run(
        ["pgrep", "-x", KARABINER_CORE_SERVICE_PROCESS_NAME],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def find_aerospace_socket_path():
    matching = glob.glob(AEROSPACE_SOCKET_GLOB_PATTERN)
    return matching[0] if matching else None


def send_aerospace_ipc_command(arguments_list):
    socket_path = find_aerospace_socket_path()
    if socket_path is None:
        return None
    client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client_socket.settimeout(2)
    try:
        client_socket.connect(socket_path)
        request_payload = json.dumps(
            {
                "args": arguments_list,
                "stdin": "",
                "windowId": None,
                "workspace": None,
            }
        ).encode()
        client_socket.sendall(request_payload)
        client_socket.shutdown(socket.SHUT_WR)
        response_bytes = b""
        while True:
            chunk = client_socket.recv(4096)
            if not chunk:
                break
            response_bytes += chunk
        client_socket.close()
        decoder = json.JSONDecoder()
        response_object, _ = decoder.raw_decode(response_bytes.decode())
        if response_object.get("exitCode", 1) != 0:
            return None
        return response_object.get("stdout", "")
    except (OSError, ValueError):
        return None


def query_aerospace_focused_window_id():
    stdout_text = send_aerospace_ipc_command(["list-windows", "--focused", "--json"])
    if not stdout_text:
        return None
    try:
        windows = json.loads(stdout_text)
        return windows[0]["window-id"] if windows else None
    except (ValueError, IndexError, KeyError):
        return None


def query_aerospace_focused_workspace_window_ids():
    stdout_text = send_aerospace_ipc_command(
        ["list-windows", "--workspace", "focused", "--json"]
    )
    if not stdout_text:
        return []
    try:
        return [w["window-id"] for w in json.loads(stdout_text)]
    except (ValueError, KeyError):
        return []


def focus_window_via_aerospace_and_wait(target_window_id):
    send_aerospace_ipc_command(["focus", "--window-id", str(target_window_id)])
    time.sleep(FOCUS_EVENT_PROPAGATION_DELAY_SECONDS)
