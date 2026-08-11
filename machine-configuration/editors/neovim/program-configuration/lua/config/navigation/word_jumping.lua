local word_jumping = {}

local word_start_pattern = [[\%(^\|\s\)\zs\S]]

local function insert_mode_is_active()
  return vim.api.nvim_get_mode().mode:find("i") ~= nil
end

local function last_reachable_column_of(line_number)
  local line_length = #vim.fn.getline(line_number)
  if insert_mode_is_active() then
    return line_length + 1
  end
  return math.max(line_length, 1)
end

local function word_start_within_the_line(search_flags, line_number)
  local found_line, found_column = unpack(vim.fn.searchpos(word_start_pattern, search_flags, line_number))
  if found_line ~= line_number then
    return nil
  end
  return found_column
end

local function move_to_column(line_number, column)
  vim.api.nvim_win_set_cursor(0, { line_number, column - 1 })
end

function word_jumping.jump_left()
  local line_number = vim.fn.line(".")
  move_to_column(line_number, word_start_within_the_line("bnW", line_number) or 1)
end

function word_jumping.jump_right()
  local line_number = vim.fn.line(".")
  local next_word_start = word_start_within_the_line("nW", line_number)
  move_to_column(line_number, next_word_start or last_reachable_column_of(line_number))
end

return word_jumping
