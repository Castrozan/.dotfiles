# Mako notification daemon configuration
# Theme-integrated via omarchy

# Font
font=JetBrainsMono Nerd Font 12

# Position
anchor=top-right
margin=10

# Size and layout
width=400
height=150
padding=12
border-size=1
border-radius=12

# Colors (using theme variables)
background-color={{ background }}e6
text-color={{ foreground }}
border-color={{ foreground }}1a

# Progress bar
progress-color=over {{ accent }}

# Urgency levels
[urgency=low]
border-color={{ foreground }}1a
background-color={{ background }}cc
text-color={{ foreground }}cc

[urgency=normal]
border-color={{ foreground }}1a
background-color={{ background }}e6
text-color={{ foreground }}

[urgency=critical]
border-color={{ color1 }}
background-color={{ background }}f2
text-color={{ color1 }}

# Behavior
default-timeout=5000
ignore-timeout=0
# max-visible can only be set per output/anchor, not globally

# Interaction
on-button-left=dismiss
on-button-middle=none
on-button-right=dismiss-all
on-touch=dismiss

# Grouping
group-by=app-name
