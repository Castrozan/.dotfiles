source ~/.dotfiles/shell/bash_aliases.sh
source ~/.dotfiles/.bash_env_vars

alias source-shell 'source ~/.dotfiles/shell/fish/config.fish'

function wildfly
  sdk use java 8.0.432-amzn
  cd /opt/wildfly-aplicacoes/bin
  ./standalone.sh $argv
end
