#!/bin/bash

# From https://gist.github.com/junegunn/f4fca918e937e6bf5bad?permalink_comment_id=3715673#gistcomment-3715673
function git_fzf() {
    set -eo pipefail
    shopt -s inherit_errexit
    cd -- "${GIT_PREFIX:-.}"
    local -a args=("$@")
    if [[ "${#args[@]}" -eq 0 ]]; then
        args+=("--graph" --glob="refs/heads/*")
    fi
    local -a show_filter
    while [[ "$#" -gt 0 ]]; do
        if [[ "$1" == "--" ]] || [[ "${#show_filter[@]}" -gt 0 ]]; then
            show_filter+=("$1")
        fi
        shift
    done
    if [[ "${show_filter[0]}" == '--' ]]; then
        show_filter=("${show_filter[@]:1}")
    fi
    export LESS='-R'
    export BAT_PAGER='less -S -R -M -i'
    export DELTA_PAGER='less -S -R -M -i'
    git log --color=always --abbrev=7 \
        --format=format:"%C(bold blue)%h%C(reset) %C(dim white)%an%C(reset)%C(bold yellow)%d%C(reset) %C(white)%s%C(reset) %C(bold green)(%ar)%C(reset)" "${args[@]}" |
        fzf --ansi --no-sort --layout=reverse --tiebreak=index \
            --preview="f() { \
                set -- \$(echo -- \$@ | rg -o '\\b[a-f0-9]{7,}\\b'); \
                [ \$# -eq 0 ] || git show --color=always --format=fuller \$1 -- \"\${show_filter[@]}\" | delta --line-numbers; \
            }; f {}" \
            --bind="ctrl-j:preview-down,ctrl-k:preview-up,ctrl-f:preview-page-down,ctrl-b:preview-page-up" \
            --bind="ctrl-m:execute: \
                (rg -o '\\b[a-f0-9]{7,}\\b' | head -1 | xargs -I % -- git show --color=always %) << 'FZFEOF'\n \
                {}\nFZFEOF" \
            --preview-window=right:60%
}
git_fzf "$@"
