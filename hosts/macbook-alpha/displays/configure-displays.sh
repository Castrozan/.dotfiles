#!/usr/bin/env bash
# Applies macOS display preferences: BezelServices auto-dim, CoreBrightness blue
# light reduction schedule, keyboard dim time. Driven by USERNAME env var.

echo "configuring display settings..." >&2

USER_UUID=$(/usr/bin/dscl . -read "/Users/$USERNAME" GeneratedUID | /usr/bin/awk '{print $2}')

/usr/bin/defaults write /Library/Preferences/com.apple.BezelServices dAuto -bool true

/usr/bin/defaults write /var/root/Library/Preferences/com.apple.CoreBrightness.plist \
	"CBUser-${USER_UUID}" \
	-dict-add CBBlueReductionStatus \
	'
  <dict>
    <key>AutoBlueReductionEnabled</key><integer>1</integer>
    <key>BlueReductionAvailable</key><integer>1</integer>
    <key>BlueReductionEnabled</key><integer>0</integer>
    <key>BlueReductionMode</key><integer>0</integer>
    <key>BlueReductionSunScheduleAllowed</key><true/>
    <key>BlueLightReductionSchedule</key>
    <dict>
      <key>DayStartHour</key><integer>7</integer>
      <key>DayStartMinute</key><integer>0</integer>
      <key>NightStartHour</key><integer>22</integer>
      <key>NightStartMinute</key><integer>0</integer>
    </dict>
    <key>Version</key><integer>1</integer>
  </dict>
  '

/usr/bin/defaults write /var/root/Library/Preferences/com.apple.CoreBrightness.plist \
	"Keyboard Dim Time" -int 0

/usr/bin/killall cfprefsd 2>/dev/null || true
