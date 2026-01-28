#!/usr/bin/env bash

# nmtui uses newt library which ignores terminal colors.
# NEWT_COLORS forces readable UI regardless of terminal theme.
export NEWT_COLORS='
root=white,black
border=white,black
window=white,black
shadow=white,black
title=white,black
button=black,cyan
actbutton=black,cyan
compactbutton=white,black
checkbox=white,black
actcheckbox=black,cyan
entry=white,black
disentry=gray,black
label=white,black
listbox=white,black
actlistbox=black,cyan
sellistbox=cyan,black
actsellistbox=black,cyan
textbox=white,black
acttextbox=black,cyan
emptyscale=white,black
fullscale=white,cyan
helpline=white,black
roottext=white,black
'

exec nmtui "$@"
