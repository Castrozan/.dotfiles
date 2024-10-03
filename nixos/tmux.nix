{ pkgs, ... }:
{
  # Global Tmux configuration
  environment.etc."tmux.conf".text = ''
    set-option -sa terminal-overrides ",xterm*:Tc"

    set -g set-clipboard on

    set -g mouse on

    # Start panes and windows at 1
    set -g base-index 1
    set -g pane-base-index 1
    set-window-option -g pane-base-index 1
    set-option -g renumber-windows on

    # Set pane name
    set -g @catppuccin_pane_status_enabled "yes"
    set -g @catppuccin_pane_border_status "top"
    set -g @catppuccin_pane_left_separator " "
    set -g @catppuccin_pane_right_separator " "
    set -g @catppuccin_pane_middle_separator " "
    set -g @catppuccin_pane_number_position "left"
    set -g @catppuccin_pane_default_fill "number"
    set -g @catppuccin_pane_default_text "#T"
    set -g @catppuccin_pane_border_style "fg=#{thm_blue}"
    set -g @catppuccin_pane_active_border_style "fg=#{thm_orange}"
    set -g @catppuccin_pane_color "fg=#{thm_blue}"
    set -g @catppuccin_pane_background_color "fg=#{thm_bg}"

    # Set window name
    set -g @catppuccin_window_current_text "#W"
    set -g @catppuccin_window_default_text "#W"

    # Bind ctrl + b, r to rename pane
    bind r command-prompt "select-pane -T '%%'"

    # Open panes in the same directory as the current pane
    bind '"' split-window -v -c "#{pane_current_path}"
    bind % split-window -h -c "#{pane_current_path}"

    # Set plugins after configuration
    # TODO: yank not working
    run-shell ${pkgs.tmuxPlugins.yank}/share/tmux-plugins/yank/yank.tmux
    run-shell ${pkgs.tmuxPlugins.sensible}/share/tmux-plugins/sensible/sensible.tmux
    run-shell ${pkgs.tmuxPlugins.catppuccin}/share/tmux-plugins/catppuccin/catppuccin.tmux
  '';
}
