#!/usr/bin/env python3
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import subprocess
import json

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

        width, height = 500, 350

        self.set_default_size(width, height)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_position(Gtk.WindowPosition.NONE)
        self.move((screen_width - width) // 2, 40)

        # Close on escape
        self.connect("key-press-event", self.on_key_press)

        # Style
        css = b"""
        window {
            background-color: #1e1e2e;
            border-radius: 12px;
            border: none;
        }
        calendar {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-size: 18px;
            padding: 12px;
            border: none;
        }
        calendar.header {
            border: none;
            background-color: #1e1e2e;
        }
        calendar:selected {
            background-color: #94e2d5;
            color: #1e1e2e;
        }
        calendar.header {
            color: #cdd6f4;
            font-weight: bold;
            font-size: 20px;
        }
        calendar.button {
            color: #89b4fa;
        }
        calendar:indeterminate {
            color: #6c7086;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        calendar = Gtk.Calendar()
        calendar.set_property("show-heading", True)
        calendar.set_property("show-day-names", True)
        calendar.set_property("show-week-numbers", False)

        self.add(calendar)

    def on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            Gtk.main_quit()

win = CalendarWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
