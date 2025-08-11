function nvm
  bass source ~/.nvm/nvm.sh --no-use ';' nvm $argv
end

set -x NVM_DIR ~/.nvm
if test -d $NVM_DIR
  nvm use default --silent ^/dev/null
end
