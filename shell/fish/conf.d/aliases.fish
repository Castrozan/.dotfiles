source ~/.dotfiles/shell/bash_aliases.sh

if test -f ~/.dotfiles/.shell_env_vars
  source ~/.dotfiles/.shell_env_vars
end

alias source-shell 'source ~/.dotfiles/shell/fish/config.fish'

function wildfly
  sdk use java 8.0.432-amzn
  cd /opt/wildfly-aplicacoes/bin
  ./standalone.sh $argv
end
