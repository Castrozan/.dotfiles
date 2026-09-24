import argparse
import ctypes
import signal
import time


class RevealCancelled(Exception):
    pass


def reveal_menu_bar(display_id):
    def cancel_reveal(_signal_number, _frame):
        raise RevealCancelled

    visibility_library = ctypes.CDLL(
        "/System/Library/PrivateFrameworks/SkyLight.framework/SkyLight"
    )
    visibility_library.SLSMainConnectionID.argtypes = ()
    visibility_library.SLSMainConnectionID.restype = ctypes.c_int
    set_visibility = visibility_library.SLSSetMenuBarVisibilityOverrideOnDisplay
    set_visibility.argtypes = (ctypes.c_int, ctypes.c_int, ctypes.c_bool)
    set_visibility.restype = ctypes.c_int
    connection_id = visibility_library.SLSMainConnectionID()
    signal.signal(signal.SIGTERM, cancel_reveal)
    signal.signal(signal.SIGINT, cancel_reveal)
    try:
        result = set_visibility(connection_id, display_id, True)
        if result != 0:
            raise RuntimeError(f"Menu bar reveal failed: {result}")
        time.sleep(1)
    except RevealCancelled:
        pass
    finally:
        result = set_visibility(connection_id, display_id, False)
        if result != 0:
            raise RuntimeError(f"Menu bar visibility release failed: {result}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("display_id", type=int)
    reveal_menu_bar(parser.parse_args().display_id)
