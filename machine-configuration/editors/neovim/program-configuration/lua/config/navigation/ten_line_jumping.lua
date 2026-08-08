local ten_line_jumping = {}

local lines_per_jump = 10

function ten_line_jumping.jump_lines_stopping_at_the_buffer_edge(line_delta)
  local current_line = vim.fn.line(".")
  local target_line = math.min(math.max(current_line + line_delta, 1), vim.fn.line("$"))
  local reachable_line_count = math.abs(target_line - current_line)
  if reachable_line_count == 0 then
    return
  end
  vim.cmd("normal! " .. reachable_line_count .. (line_delta > 0 and "j" or "k") .. "zz")
end

function ten_line_jumping.jump_buffer_down()
  ten_line_jumping.jump_lines_stopping_at_the_buffer_edge(lines_per_jump)
end

function ten_line_jumping.jump_buffer_up()
  ten_line_jumping.jump_lines_stopping_at_the_buffer_edge(-lines_per_jump)
end

function ten_line_jumping.jump_snacks_selection_down(picker)
  picker.list:move(lines_per_jump)
end

function ten_line_jumping.jump_snacks_selection_up(picker)
  picker.list:move(-lines_per_jump)
end

function ten_line_jumping.jump_telescope_selection_down(prompt_buffer_number)
  require("telescope.actions.set").shift_selection(prompt_buffer_number, lines_per_jump)
end

function ten_line_jumping.jump_telescope_selection_up(prompt_buffer_number)
  require("telescope.actions.set").shift_selection(prompt_buffer_number, -lines_per_jump)
end

return ten_line_jumping
