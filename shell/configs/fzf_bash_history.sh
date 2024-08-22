#!/bin/bash
# Fuzzy find history search
# ctrl-f to search history
# enter to select command
# Inspired from https://github.com/junegunn/fzf/wiki/examples#searching-file-contents

bind '"\C-f": "\C-x1\e^\er"'
bind -x '"\C-x1": __fzf_history';

__fzf_history () {
    __ehc $(
        history | 
        fzf --tac --tiebreak=index --height 40% --layout=reverse --border | 
        perl -ne 'm/^\s*([0-9]+)/ and print "!$1"'
    )
}

__ehc() {
    if [ -n "$1" ] ; then
        bind '"\er": redraw-current-line'
        bind '"\e^": magic-space'
        READLINE_LINE=${READLINE_LINE:+${READLINE_LINE:0:READLINE_POINT}}${1}${READLINE_LINE:+${READLINE_LINE:READLINE_POINT}}
        READLINE_POINT=$(( READLINE_POINT + ${#1} ))
    else
        bind '"\er":'
        bind '"\e^":'
    fi
}