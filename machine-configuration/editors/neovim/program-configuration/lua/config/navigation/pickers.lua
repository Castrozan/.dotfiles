local pickers = {}

function pickers.find_files()
  require("telescope.builtin").find_files()
end

function pickers.commands()
  require("telescope.builtin").commands()
end

function pickers.live_grep()
  require("telescope.builtin").live_grep()
end

function pickers.document_symbols()
  require("telescope.builtin").lsp_document_symbols()
end

function pickers.workspace_symbols()
  require("telescope.builtin").lsp_dynamic_workspace_symbols()
end

function pickers.references()
  require("telescope.builtin").lsp_references()
end

return pickers
