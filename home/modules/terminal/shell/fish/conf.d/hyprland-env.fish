# Fix stale HYPRLAND_INSTANCE_SIGNATURE after Hyprland restart
# This is needed because tmux resurrect preserves old env vars
# Socket files can exist but be dead after crash, so we test connectivity

function __fix_hyprland_env
    # Only run in Wayland session
    if not set -q WAYLAND_DISPLAY
        return
    end

    # Skip if not in tmux (direct terminals get fresh env)
    if not set -q TMUX
        return
    end

    # Skip if no Hyprland signature set
    if not set -q HYPRLAND_INSTANCE_SIGNATURE
        return
    end

    # Test if hyprctl actually works (socket file can exist but be dead)
    if hyprctl monitors &>/dev/null
        return  # Connection works, env is valid
    end

    # Find the current valid Hyprland instance
    set -l hypr_dir "/run/user/"(id -u)"/hypr"
    if not test -d "$hypr_dir"
        return
    end

    # Try each instance (newest first) to find one that works
    for sig in (ls -t "$hypr_dir" 2>/dev/null)
        set -l test_socket "$hypr_dir/$sig/.socket.sock"
        if test -S "$test_socket"
            # Test if this socket actually works by trying hyprctl
            set -lx HYPRLAND_INSTANCE_SIGNATURE "$sig"
            if hyprctl monitors &>/dev/null
                set -gx HYPRLAND_INSTANCE_SIGNATURE "$sig"
                return
            end
        end
    end
end

# Run once on shell start
if status is-interactive
    __fix_hyprland_env
end
