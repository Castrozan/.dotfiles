# Aliases file for bash shell

# aliases personal
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'
alias code="code . -n"
alias lc="ls -a --color=never"
alias oo="cd $OBSIDIAN_HOME && nvim ."
alias studio3t="cd ~/studio3t && ./Studio-3T .sh"
alias nvim="$HOME/nvim.appimage"
alias vim="$HOME/nvim.appimage"
alias bashrc="nvim ~/.bashrc"
alias dotfiles="cd ~/.dotfiles_ubuntu"
alias source-bash="source ~/.bashrc"
alias obsidian="flatpak run md.obsidian.Obsidian >/dev/null 2>&1 &"
alias t="tmux"
alias todo="cd $HOME/Documents/obsidianVault && nvim TODO.md"
alias scripts="cd $HOME/repo/scripts && nvim ."
alias g="lazygit"
alias d="lazydocker"

# TODO: add third party aliases to a separated file
# aliases Betha
alias k="kubectl"
alias standalone="cd /opt/wildfly-aplicacoes/standalone/configuration"
export FLY_HOME=/home/lucas.zanoni/betha-fly
alias fly-java6='sdk use java 1.6.0_45-fly; sdk use maven 3.2.3-fly'
alias fly-jboss='/home/lucas.zanoni/betha-fly/tools/jboss-5.1.0.GA/bin/run.sh -c betha'
alias wildfly='cd /opt/wildfly-aplicacoes/bin; ./standalone.sh'
alias fly-java6='sdk use java 1.6.0_45-fly; sdk use maven 3.2.3-fly'
alias jboss='/home/lucas.zanoni/betha-fly/tools/jboss-5.1.0.GA/bin/run.sh -c betha'alias killport='sh /home/lucas.zanoni/.local/bin/killport'
alias vt_prod='aws sso login --profile eks-plataforma-production'
alias vt_test='aws sso login --profile eks-plataforma-test'
alias studio3t="cd ~/studio3t && ./Studio-3T .sh"