from pathlib import Path


DOTFILES_ROOT = Path(__file__).resolve().parents[5]
CLIPSE_MODULE = DOTFILES_ROOT / "home/linux/desktop/clipse.nix"
CLIPSE_WAYLAND_LISTENER = (
    DOTFILES_ROOT / "home/linux/desktop/scripts/clipse-wayland-listener"
)
HYPRLAND_AUTOSTART = DOTFILES_ROOT / ".config/hypr/conf.d/autostart.conf"
GRAPHICAL_SERVICES_ACTIVATION_MODULE = (
    DOTFILES_ROOT / "home/linux/hyprland/graphical-services-activation.nix"
)


def test_the_clipse_service_runs_wayland_clipboard_watchers():
    clipse_module_source = CLIPSE_MODULE.read_text()
    clipse_wayland_listener_source = CLIPSE_WAYLAND_LISTENER.read_text()

    assert 'ConditionEnvironment = "WAYLAND_DISPLAY";' in clipse_module_source
    assert "--listen-shell" not in clipse_module_source
    assert "builtins.readFile ./scripts/clipse-wayland-listener" in clipse_module_source
    assert (
        '"CLIPSE_WL_PASTE_BINARY=${pkgs.wl-clipboard}/bin/wl-paste"'
        in clipse_module_source
    )
    assert '"CLIPSE_BINARY=${clipse-zanoni}/bin/clipse"' in clipse_module_source
    assert (
        '"$CLIPSE_WL_PASTE_BINARY" --type text --watch "$CLIPSE_BINARY" --wl-store'
        in (clipse_wayland_listener_source)
    )
    assert (
        '"$CLIPSE_WL_PASTE_BINARY" --type image/png --watch "$CLIPSE_BINARY" --wl-store'
        in (clipse_wayland_listener_source)
    )
    assert "wait -n" in clipse_wayland_listener_source


def test_hyprland_starts_clipse_after_importing_the_wayland_environment():
    hyprland_autostart_source = HYPRLAND_AUTOSTART.read_text()

    assert "clipse.service" in hyprland_autostart_source
    assert hyprland_autostart_source.index("systemctl --user import-environment") < (
        hyprland_autostart_source.index("clipse.service")
    )


def test_rebuild_activation_restarts_the_clipse_listener():
    graphical_services_activation_source = (
        GRAPHICAL_SERVICES_ACTIVATION_MODULE.read_text()
    )

    assert '"clipse.service"' in graphical_services_activation_source
