local command_line_abbreviations = {}

local shifted_typo_corrections = {
  W = "w",
  Q = "q",
  Wq = "wq",
  WQ = "wq",
}

function command_line_abbreviations.install()
  for typed_command, intended_command in pairs(shifted_typo_corrections) do
    vim.cmd("cnoreabbrev " .. typed_command .. " " .. intended_command)
  end
end

return command_line_abbreviations
