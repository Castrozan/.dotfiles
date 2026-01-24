#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import subprocess
import json
import os
try:
    import tomllib
except ImportError:
    import tomli as tomllib

def load_theme_colors():
    colors_path = os.path.expanduser("~/.config/omarchy/current/theme/colors.toml")
    defaults = {
        "background": "#1e1e2e",
        "foreground": "#cdd6f4",
        "color4": "#89b4fa",
        "color6": "#94e2d5",
        "color8": "#6c7086",
    }
    try:
        with open(colors_path, "rb") as f:
            colors = tomllib.load(f)
            return {**defaults, **colors}
    except:
        return defaults

class CalendarWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="Calendar")

        # Get monitor width for centering
        try:
            result = subprocess.run(['hyprctl', 'monitors', '-j'], capture_output=True, text=True)
            monitors = json.loads(result.stdout)
            screen_width = monitors[0]['width']
        except:
            screen_width = 1920

        width, height = 540, 350

        self.set_default_size(width, height)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_position(Gtk.WindowPosition.NONE)
        self.move((screen_width - width) // 2, 40)

        # Close on escape
        self.connect("key-press-event", self.on_key_press)

        # Load theme colors
        c = load_theme_colors()

        # Style
        css = f"""
        window {{
            background-color: {c['background']};
            border-radius: 12px;
            border: none;
        }}
        calendar {{
            background-color: {c['background']};
            color: {c['foreground']};
            font-size: 18px;
            padding: 12px;
            border: none;
        }}
        calendar.header {{
            border: none;
            background-color: {c['background']};
        }}
        calendar:selected {{
            background-color: {c['accent']};
            color: {c['background']};
        }}
        calendar.header {{
            color: {c['foreground']};
            font-weight: bold;
            font-size: 20px;
        }}
        calendar.button {{
            color: {c['color4']};
        }}
        calendar:indeterminate {{
            color: {c['color8']};
        }}
        button.close {{
            background: {c['accent']};
            background-color: {c['accent']};
            background-image: none;
            border: none;
            border-radius: 6px;
            color: {c['background']};
            padding: 4px 10px;
            min-width: 0;
            min-height: 0;
            font-weight: bold;
        }}
        button.close label {{
            color: {c['background']};
        }}
        button.close:hover {{
            background: {c['color4']};
            background-color: {c['color4']};
            background-image: none;
        }}
        """.encode()
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        # Main container
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Header row with close button at far right
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        header.set_margin_top(8)
        header.set_margin_end(10)

        # Spacer to push close button to the right
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header.pack_start(spacer, True, True, 0)

        # Close button
        close_btn = Gtk.Button(label="✕")
        close_btn.get_style_context().add_class("close")
        close_btn.connect("clicked", lambda x: Gtk.main_quit())
        header.pack_end(close_btn, False, False, 0)

        vbox.pack_start(header, False, False, 0)

        # Calendar
        calendar = Gtk.Calendar()
        calendar.set_property("show-heading", True)
        calendar.set_property("show-day-names", True)
        calendar.set_property("show-week-numbers", False)
        vbox.pack_start(calendar, True, True, 0)

        self.add(vbox)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

win = CalendarWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
