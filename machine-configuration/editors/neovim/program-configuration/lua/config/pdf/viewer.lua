local M = {}
local documents = {}
local Layout = require("config.pdf.page_layout")
local DocumentView = require("config.pdf.document_view")

local function show_message(buffer, message)
  vim.bo[buffer].modifiable = true
  vim.api.nvim_buf_set_lines(buffer, 0, -1, false, vim.split(message, "\n", { plain = true }))
  vim.bo[buffer].modifiable = false
  vim.bo[buffer].modified = false
end

local function close_document(buffer)
  local document = documents[buffer]
  documents[buffer] = nil
  if not document then
    return
  end
  if document.process then
    document.process:kill(15)
  end
  if document.view then
    document.view:close()
  end
end

local function open_document(buffer)
  close_document(buffer)
  local document = { path = vim.api.nvim_buf_get_name(buffer) }
  documents[buffer] = document
  vim.bo[buffer].buftype = "nowrite"
  vim.bo[buffer].swapfile = false
  vim.bo[buffer].filetype = "image"
  show_message(buffer, "Loading PDF…")
  for _, executable in ipairs({ "pdfinfo", "magick", "gs" }) do
    if vim.fn.executable(executable) ~= 1 then
      show_message(buffer, "PDF viewer requires " .. executable .. ". Rebuild the Neovim configuration.")
      return
    end
  end
  Snacks.image.terminal.detect(function()
    if documents[buffer] ~= document then
      return
    end
    if not Snacks.image.supports_terminal() or not Snacks.image.terminal.env().placeholders then
      show_message(
        buffer,
        "PDF scrolling requires Kitty graphics with Unicode placeholders, as in Herdr, Kitty, or Ghostty."
      )
      return
    end
    document.process = vim.system(
      { "pdfinfo", "-f", "1", "-l", "-1", document.path },
      { text = true, timeout = 10000, env = { LC_ALL = "C" } },
      vim.schedule_wrap(function(result)
        if documents[buffer] ~= document then
          return
        end
        document.process = nil
        local sizes = Layout.parse(result.stdout or "")
        if result.code ~= 0 or not sizes then
          local reason = result.stderr and result.stderr ~= "" and result.stderr or "Invalid PDF page dimensions"
          show_message(buffer, "Unable to open PDF:\n" .. reason)
          return
        end
        document.view = DocumentView.new(buffer, document.path, sizes)
        document.view:update()
      end)
    )
  end)
end

function M.setup()
  local group = vim.api.nvim_create_augroup("PdfViewer", { clear = true })
  vim.api.nvim_create_autocmd("BufReadCmd", {
    group = group,
    pattern = "*.[pP][dD][fF]",
    callback = function(event)
      open_document(event.buf)
    end,
  })
  vim.api.nvim_create_autocmd({ "BufDelete", "BufWipeout" }, {
    group = group,
    callback = function(event)
      close_document(event.buf)
    end,
  })
  local refresh_pending = false
  vim.api.nvim_create_autocmd({ "WinScrolled", "WinResized", "BufWinEnter", "BufWinLeave", "WinClosed", "TabEnter" }, {
    group = group,
    callback = function()
      if refresh_pending or not next(documents) then
        return
      end
      refresh_pending = true
      vim.defer_fn(function()
        refresh_pending = false
        for _, document in pairs(documents) do
          if document.view then
            document.view:update()
          end
        end
      end, 30)
    end,
  })
end

return M
