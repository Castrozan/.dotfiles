from pathlib import Path
import threading

from ambient_canvas_theme import resolve_theme_background_color

THEME_POLL_INTERVAL_SECONDS = 1.0
COLOR_CHANNEL_MAXIMUM = 255
HEX_CHANNEL_OFFSETS = (1, 3, 5)


def build_screen_blend_shader(background_hex):
    red, green, blue = (
        int(background_hex[offset : offset + 2], 16) / COLOR_CHANNEL_MAXIMUM
        for offset in HEX_CHANNEL_OFFSETS
    )
    return f"""//!HOOK OUTPUT
//!BIND HOOKED
vec4 hook() {{
    vec3 backdrop = vec3({red:.6f}, {green:.6f}, {blue:.6f});
    vec3 content = HOOKED_tex(HOOKED_pos).rgb;
    return vec4(vec3(1.0) - (vec3(1.0) - content) * (vec3(1.0) - backdrop), 1.0);
}}
"""


class ThemeScreenBlend:
    def __init__(self, mpv_client, theme_colors_path, shader_directory):
        self.mpv_client = mpv_client
        self.theme_colors_path = theme_colors_path
        self.shader_directory = Path(shader_directory)
        self._applied_background_hex = None
        self._applied_shader_path = None
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._watch_theme, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=3)

    def synchronize(self):
        background_hex = resolve_theme_background_color(self.theme_colors_path)
        if background_hex == self._applied_background_hex:
            return
        shader_path = self.shader_directory / f"theme-{background_hex[1:]}.glsl"
        shader_path.write_text(build_screen_blend_shader(background_hex))
        self.mpv_client.send_command(
            ["change-list", "glsl-shaders", "set", str(shader_path)]
        )
        if self._applied_shader_path is not None:
            self._applied_shader_path.unlink(missing_ok=True)
        self._applied_background_hex = background_hex
        self._applied_shader_path = shader_path

    def _watch_theme(self):
        while not self._stop_event.is_set():
            self.synchronize()
            self._stop_event.wait(THEME_POLL_INTERVAL_SECONDS)
