import types


def build_screen(origin_x, origin_y, height, visible_height=None):
    return types.SimpleNamespace(
        frame=lambda: types.SimpleNamespace(
            origin=types.SimpleNamespace(x=origin_x, y=origin_y),
            size=types.SimpleNamespace(height=height),
        ),
        visibleFrame=lambda: types.SimpleNamespace(
            origin=types.SimpleNamespace(x=origin_x, y=origin_y),
            size=types.SimpleNamespace(height=visible_height),
        ),
    )
