use ratatui::style::Color;

const CATPPUCCIN_TEXT: Color = Color::Rgb(205, 214, 244);
const CATPPUCCIN_SUBTEXT: Color = Color::Rgb(166, 173, 200);
const CATPPUCCIN_OVERLAY: Color = Color::Rgb(127, 132, 156);
const CATPPUCCIN_SURFACE: Color = Color::Rgb(69, 71, 90);
const CATPPUCCIN_BLUE: Color = Color::Rgb(137, 180, 250);
const CATPPUCCIN_LAVENDER: Color = Color::Rgb(180, 190, 254);
const CATPPUCCIN_MAUVE: Color = Color::Rgb(203, 166, 247);
const CATPPUCCIN_PEACH: Color = Color::Rgb(250, 179, 135);

#[derive(Debug, Default, Clone, Copy)]
pub struct Theme {
    pub button_keyboard_label: Color,
    pub button_label: Color,
    pub debug: Color,
    pub details_border: Color,
    pub details_field_fg: Color,
    pub details_hint_fg: Color,
    pub menu_bg: Color,
    pub menu_button_background: Color,
    pub menu_button_highlight: Color,
    pub menu_button_keyboard_label: Color,
    pub menu_button_label: Color,
    pub menu_button_shadow: Color,
    pub menu_logo_fg: Color,
    pub popup_border: Color,
    pub search_bg: Color,
    pub search_border: Color,
    pub standard_bg: Color,
    pub standard_fg: Color,
    pub status_bar_bg: Color,
    pub status_bar_fg: Color,
    pub table_alt_row: Color,
    pub table_buffer_bg: Color,
    pub table_header_bg: Color,
    pub table_header_fg: Color,
    pub table_normal_row: Color,
    pub table_pattern_highlight_bg: Color,
    pub table_row_fg: Color,
    pub table_selected_cell_style_fg: Color,
    pub table_selected_column_style_fg: Color,
    pub table_selected_row_style_fg: Color,
    pub table_track_bg: Color,
    pub table_track_fg: Color,
}

impl Theme {
    pub fn new() -> Self {
        Self {
            button_keyboard_label: CATPPUCCIN_SUBTEXT,
            button_label: CATPPUCCIN_TEXT,
            debug: CATPPUCCIN_BLUE,
            details_border: CATPPUCCIN_SURFACE,
            details_field_fg: CATPPUCCIN_TEXT,
            details_hint_fg: CATPPUCCIN_OVERLAY,
            menu_bg: Color::Reset,
            menu_button_background: Color::Reset,
            menu_button_highlight: CATPPUCCIN_SURFACE,
            menu_button_keyboard_label: CATPPUCCIN_SUBTEXT,
            menu_button_label: CATPPUCCIN_TEXT,
            menu_button_shadow: Color::Reset,
            menu_logo_fg: CATPPUCCIN_MAUVE,
            popup_border: CATPPUCCIN_BLUE,
            search_bg: Color::Reset,
            search_border: CATPPUCCIN_BLUE,
            standard_bg: Color::Reset,
            standard_fg: CATPPUCCIN_TEXT,
            status_bar_bg: Color::Reset,
            status_bar_fg: CATPPUCCIN_TEXT,
            table_alt_row: Color::Reset,
            table_buffer_bg: Color::Reset,
            table_header_bg: Color::Reset,
            table_header_fg: CATPPUCCIN_BLUE,
            table_normal_row: Color::Reset,
            table_pattern_highlight_bg: CATPPUCCIN_SURFACE,
            table_row_fg: CATPPUCCIN_TEXT,
            table_selected_cell_style_fg: CATPPUCCIN_PEACH,
            table_selected_column_style_fg: CATPPUCCIN_LAVENDER,
            table_selected_row_style_fg: CATPPUCCIN_LAVENDER,
            table_track_bg: Color::Reset,
            table_track_fg: CATPPUCCIN_OVERLAY,
        }
    }
}
