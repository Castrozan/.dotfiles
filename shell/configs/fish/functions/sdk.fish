function sdk
    if not set -q SDKMAN_DIR
        export SDKMAN_DIR="$HOME/.sdkman"
    end
    
    set -l sdk_bash_path (command -v bash)
    set -l sdk_init_path "$SDKMAN_DIR/bin/sdkman-init.sh"

    if test -f "$sdk_init_path"
        $sdk_bash_path -c "source '$sdk_init_path'; sdk $argv"
    else
        echo "SDKMAN not found."
    end
end
