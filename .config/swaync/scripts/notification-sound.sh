#!/usr/bin/env bash
[ -f "$HOME/.cache/notification-mute" ] && exit 0
canberra-gtk-play -i message-new-instant &
