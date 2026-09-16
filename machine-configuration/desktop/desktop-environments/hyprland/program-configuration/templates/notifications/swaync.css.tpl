@define-color foreground {{ foreground }};
@define-color background {{ background }};
@define-color accent {{ accent }};
@define-color dim {{ color8 }};
@define-color surface {{ selection_background }};
@define-color error {{ color1 }};

* {
  font-family: "JetBrainsMono Nerd Font", monospace;
  font-weight: 500;
  font-size: 14px;
}

.control-center {
  background: alpha(@background, 0.9);
  border-radius: 12px;
  border: 1px solid alpha(@foreground, 0.1);
  margin: 10px;
  padding: 10px;
}

.control-center .widget-title {
  color: @foreground;
  font-size: 1.2em;
  font-weight: bold;
  margin: 8px;
}

.control-center .widget-title > button {
  background: alpha(@foreground, 0.1);
  border-radius: 8px;
  border: none;
  padding: 6px 12px;
  color: @foreground;
}

.control-center .widget-title > button:hover {
  background: alpha(@foreground, 0.2);
}

.control-center .widget-dnd {
  margin: 8px;
  padding: 4px;
  color: @foreground;
}

.control-center .widget-dnd > label {
  color: @foreground;
}

.control-center .widget-dnd > switch {
  background: alpha(@foreground, 0.1);
  border-radius: 12px;
}

.control-center .widget-dnd > switch:checked {
  background: @accent;
}

.control-center .widget-dnd > switch slider {
  background: @foreground;
  border-radius: 50%;
}

.control-center .notification-row {
  margin: 4px 0;
}

.control-center .notification-row .notification {
  background: alpha(@foreground, 0.05);
  border-radius: 10px;
  padding: 8px;
  margin: 2px 0;
}

.control-center .notification-row .notification:hover {
  background: alpha(@foreground, 0.1);
}

.notification-window {
  background: transparent;
}

.notification {
  background: alpha(@background, 0.95);
  border-radius: 12px;
  border: 1px solid alpha(@foreground, 0.1);
  padding: 12px;
  margin: 6px 10px;
}

.notification .notification-content {
  margin: 4px;
}

.notification .summary {
  color: @foreground;
  font-weight: bold;
  font-size: 1em;
}

.notification .body {
  color: alpha(@foreground, 0.8);
  font-size: 0.9em;
}

.notification .time {
  color: @dim;
  font-size: 0.8em;
}

.notification .image {
  border-radius: 8px;
  margin-right: 10px;
}

.notification .notification-action {
  background: alpha(@foreground, 0.1);
  border-radius: 6px;
  border: none;
  padding: 4px 8px;
  margin: 2px;
  color: @foreground;
}

.notification .notification-action:hover {
  background: alpha(@foreground, 0.2);
}

.notification .close-button {
  background: alpha(@error, 0.2);
  border-radius: 50%;
  border: none;
  min-width: 24px;
  min-height: 24px;
  padding: 0;
}

.notification .close-button:hover {
  background: @error;
}

.notification.critical {
  border: 1px solid @error;
}

.notification.critical .summary {
  color: @error;
}

.notification.low {
  opacity: 0.8;
}

.control-center .widget-mpris {
  background: alpha(@foreground, 0.05);
  border-radius: 10px;
  padding: 10px;
  margin: 8px;
}

.control-center .widget-mpris .widget-mpris-player {
  padding: 6px;
}

.control-center .widget-mpris .widget-mpris-title {
  font-weight: bold;
  font-size: 1em;
}

.control-center .widget-mpris .widget-mpris-subtitle {
  font-size: 0.9em;
  color: @dim;
}

.control-center .widget-mpris > box > button {
  background: alpha(@foreground, 0.1);
  border-radius: 50%;
  border: none;
  min-width: 36px;
  min-height: 36px;
}

.control-center .widget-mpris > box > button:hover {
  background: alpha(@foreground, 0.2);
}

.blank-window {
  background: transparent;
}

list, listview, row {
  background: transparent;
  box-shadow: none;
}
