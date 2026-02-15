set -g __NIX_MEMORY_LIMIT 16G

function nix --wraps nix
    set -l nix_binary (command -s nix)

    if command -q systemd-run; and test -n "$DBUS_SESSION_BUS_ADDRESS"
        systemd-run --user --scope -q \
            -p MemoryMax=$__NIX_MEMORY_LIMIT \
            -- $nix_binary $argv
    else
        $nix_binary $argv
    end
end
