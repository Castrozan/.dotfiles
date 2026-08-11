local missing_imports = {}

local phrases_that_mean_the_action_is_not_this_one_import = { "remove", "unused", "delete", "all missing", "organize" }

local function action_adds_an_import(action)
  local title = (action.title or ""):lower()
  if not title:find("import", 1, true) then
    return false
  end
  for _, rejected_phrase in ipairs(phrases_that_mean_the_action_is_not_this_one_import) do
    if title:find(rejected_phrase, 1, true) then
      return false
    end
  end
  return true
end

local function diagnostics_under_the_cursor()
  local line_number, column = unpack(vim.api.nvim_win_get_cursor(0))
  return vim.tbl_filter(function(diagnostic)
    return diagnostic.col <= column and column <= (diagnostic.end_col or diagnostic.col)
  end, vim.diagnostic.get(0, { lnum = line_number - 1 }))
end

function missing_imports.add()
  local reported_here = diagnostics_under_the_cursor()
  local context = #reported_here > 0 and { diagnostics = vim.lsp.diagnostic.from(reported_here) } or nil
  vim.lsp.buf.code_action({ apply = true, filter = action_adds_an_import, context = context })
end

return missing_imports
