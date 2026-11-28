#!/usr/bin/env python3

import colorsys
import sys

hex_color = sys.argv[1]
red = int(hex_color[0:2], 16) / 255
green = int(hex_color[2:4], 16) / 255
blue = int(hex_color[4:6], 16) / 255

hue_normalized, saturation, _ = colorsys.rgb_to_hsv(red, green, blue)
hue_degrees = hue_normalized * 360

if saturation < 0.1:
    print(-1)
elif hue_degrees < 15 or hue_degrees >= 345:
    print(0)
elif hue_degrees < 45:
    print(1)
elif hue_degrees < 75:
    print(2)
elif hue_degrees < 165:
    print(3)
elif hue_degrees < 255:
    print(4)
elif hue_degrees < 300:
    print(5)
else:
    print(6)
