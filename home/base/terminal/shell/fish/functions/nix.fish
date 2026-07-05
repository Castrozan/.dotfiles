set -g __NIX_MEMORY_HIGH 45%
set -g __NIX_MEMORY_MAX 55%
set -g __NIX_MEMORY_SWAP_MAX 0

function nix --wraps nix
    set -l nix_binary (command -s nix)

    if command -q systemd-run; and test -n "$DBUS_SESSION_BUS_ADDRESS"
        systemd-run --user --scope -q \
            -p MemoryHigh=$__NIX_MEMORY_HIGH \
            -p MemoryMax=$__NIX_MEMORY_MAX \
            -p MemorySwapMax=$__NIX_MEMORY_SWAP_MAX \
            -- $nix_binary $argv
    else
        $nix_binary $argv
    end
end
