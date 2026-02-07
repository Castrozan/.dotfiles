# Mako notification daemon configuration
# Theme-integrated via hypr-theme-set

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

# Behavior (MUST be before [criteria] sections!)
default-timeout=15000
ignore-timeout=0

# Interaction
on-button-left=invoke-default-action
on-button-middle=dismiss-all
on-button-right=dismiss
on-touch=invoke-default-action

# Grouping
group-by=app-name

# Urgency-specific overrides (sections below override global settings)
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
