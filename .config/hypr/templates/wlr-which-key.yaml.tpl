font: JetBrainsMono Nerd Font 14
background: "{{ background }}e6"
color: "{{ foreground }}"
border: "{{ accent }}"
separator: " → "
border_width: 2
corner_r: 12
padding: 15
anchor: center

menu:
  - key: s
    desc: Screenshot
    submenu:
      - key: s
        desc: Region (annotate)
        cmd: hypr-screenshot annotate
      - key: w
        desc: Window
        cmd: hyprshot -m window
      - key: m
        desc: Monitor
        cmd: hyprshot -m output
      - key: c
        desc: Color picker
        cmd: pkill hyprpicker || hyprpicker -a
      - key: v
        desc: Video record
        cmd: pkill wf-recorder || wf-recorder -g "$(slurp)" -f ~/Videos/recording-$(date +%Y%m%d-%H%M%S).mp4

  - key: n
    desc: Notifications
    submenu:
      - key: d
        desc: Dismiss one
        cmd: makoctl dismiss
      - key: a
        desc: Clear all
        cmd: makoctl dismiss --all
      - key: n
        desc: Toggle DND
        cmd: makoctl set-mode -t do-not-disturb

  - key: t
    desc: Tools
    submenu:
      - key: n
        desc: Network
        cmd: hypr-network
      - key: b
        desc: Bluetooth
        cmd: wezterm start -- bluetui
      - key: m
        desc: Monitor (btop)
        cmd: wezterm start -- btop
      - key: a
        desc: Audio mixer
        cmd: wezterm start -- wiremix
      - key: c
        desc: Clock
        cmd: notify-send "$(date +"%A %H:%M  —  %d %B %Y")"

  - key: a
    desc: Apps
    submenu:
      - key: b
        desc: Brave
        cmd: brave
      - key: f
        desc: Firefox
        cmd: firefox
      - key: c
        desc: Chromium
        cmd: chromium
      - key: w
        desc: Workbench
        cmd: code $HOME/workbench
      - key: n
        desc: Neovim
        cmd: wezterm -e nvim
      - key: d
        desc: Daily note
        cmd: bash -c 'OBSIDIAN_HOME="$HOME/vault" EDITOR=code daily-note'
      - key: r
        desc: Read it later
        cmd: xdg-open 'obsidian://adv-uri?commandid=obsidian-read-it-later%3Asave-clipboard-to-notice'
      - key: y
        desc: Calendar
        cmd: ~/.config/waybar/calendar-toggle.sh
      - key: t
        desc: Tmux session
        cmd: wezterm start -- tmux new-session
      - key: e
        desc: Emoji
        cmd: BEMOJI_PICKER_CMD="fuzzel --dmenu" bemoji -t
      - key: s
        desc: Spotify
        cmd: spotify
      - key: o
        desc: OBS
        cmd: obs
      - key: i
        desc: Discord
        cmd: discord
      - key: k
        desc: Calculator
        cmd: gnome-calculator
      - key: g
        desc: GIMP
        cmd: gimp
      - key: v
        desc: VLC
        cmd: vlc
      - key: l
        desc: Slack
        cmd: slack
      - key: p
        desc: Postman
        cmd: postman

  - key: w
    desc: Window
    submenu:
      - key: t
        desc: Toggle tile/group
        cmd: hypr-toggle-group-for-all-workspace-windows
      - key: d
        desc: Show desktop
        cmd: hypr-show-desktop
      - key: g
        desc: Detach from group
        cmd: hyprctl dispatch moveoutofgroup
      - key: s
        desc: Toggle split
        cmd: hyprctl dispatch togglesplit
      - key: p
        desc: Pseudo
        cmd: hyprctl dispatch pseudo
      - key: o
        desc: Pop out (float+pin)
        cmd: hyprctl dispatch togglefloating && hyprctl dispatch pin
      - key: f
        desc: True fullscreen
        cmd: hyprctl dispatch fullscreen 0
      - key: m
        desc: Maximize
        cmd: hyprctl dispatch fullscreen 1
      - key: a
        desc: Toggle opacity
        cmd: hyprctl dispatch setprop "address:$(hyprctl activewindow -j | jq -r '.address')" opaque toggle

  - key: y
    desc: Style
    submenu:
      - key: b
        desc: Next background
        cmd: hypr-theme-bg-next
      - key: t
        desc: Theme menu
        cmd: hypr-menu theme
      - key: w
        desc: Toggle waybar
        cmd: pkill waybar || waybar

  - key: l
    desc: Lock
    cmd: hyprlock --grace 1

  - key: v
    desc: Clipboard history
    cmd: wezterm start -- clipse
