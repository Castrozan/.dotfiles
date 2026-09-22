#!/usr/bin/env bash

# Load the acpi_call module
modprobe acpi_call

printf '%s\n' '\_SB.AMW3.WMAX 0 0x25 { 1, 0, 0, 0}' | tee /proc/acpi/call
printf '%s\n' '\_SB.PCI0.LPC0.EC0._Q14' | tee /proc/acpi/call
printf '%s\n' '\_SB.AMW3.WMAX 0 0x25 { 2, 0, 0, 0}' | tee /proc/acpi/call

# Capture the output and remove any null bytes
game_shift_status=$(tr -d '\0' </proc/acpi/call)
cpu_boost_path=/sys/devices/system/cpu/cpufreq/boost

if [[ "$game_shift_status" == "0x0" ]]; then
	printf '0\n' >"$cpu_boost_path"
	printf 'gmode is OFF\n'
else
	printf '1\n' >"$cpu_boost_path"
	printf 'gmode is ON\n'
fi
