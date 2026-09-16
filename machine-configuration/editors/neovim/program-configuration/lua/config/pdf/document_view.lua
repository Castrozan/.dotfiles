local Layout = require("config.pdf.page_layout")
local M = {}
M.__index = M
local namespace = vim.api.nvim_create_namespace("PdfPageErrors")
local density, maximum_pixels = 144, 1920

M.conversion_arguments = {
  "-density",
  density,
  "-define",
  "pdf:use-cropbox=true",
  "{src}[{page}]",
  "-background",
  "white",
  "-alpha",
  "remove",
  "-resize",
  maximum_pixels .. "x" .. maximum_pixels .. ">",
}

function M.new(buffer, path, sizes)
  return setmetatable({ buffer = buffer, path = path, sizes = sizes, placements = {}, files = {}, failures = {} }, M)
end

function M:clear_placements()
  for _, placement in pairs(self.placements) do
    placement:close()
  end
  self.placements = {}
end

function M:close()
  self.closed = true
  if self.conversion then
    self.conversion:abort()
  end
  self:clear_placements()
  if vim.api.nvim_buf_is_valid(self.buffer) then
    vim.api.nvim_buf_clear_namespace(self.buffer, namespace, 0, -1)
  end
end

function M:resize(windows)
  local width = 160
  for _, window in ipairs(windows) do
    width = math.min(width, math.max(1, vim.api.nvim_win_get_width(window) - 2))
    for option, value in pairs(Snacks.image.config.wo) do
      vim.wo[window][option] = value
    end
  end
  local terminal = Snacks.image.terminal.size()
  if self.width == width and vim.deep_equal(self.terminal, terminal) then
    return
  end
  local views = {}
  for _, window in ipairs(windows) do
    vim.api.nvim_win_call(window, function()
      views[window] = vim.fn.winsaveview()
    end)
  end
  local previous = self.pages
  local sizes = {}
  for _, size in ipairs(self.sizes) do
    local scale = math.min(density / 72, maximum_pixels / size.width, maximum_pixels / size.height)
    sizes[#sizes + 1] = Snacks.image.util.fit(nil, { width = width, height = 200 }, {
      info = {
        size = { width = math.floor(size.width * scale + 0.5), height = math.floor(size.height * scale + 0.5) },
        dpi = { width = density, height = density },
      },
    })
  end
  local pages, lines = Layout.build(sizes)
  self:clear_placements()
  vim.api.nvim_buf_clear_namespace(self.buffer, namespace, 0, -1)
  self.width, self.terminal, self.pages = width, terminal, pages
  vim.bo[self.buffer].modifiable = true
  vim.api.nvim_buf_set_lines(self.buffer, 0, -1, false, lines)
  vim.bo[self.buffer].modifiable = false
  vim.bo[self.buffer].modified = false
  if previous then
    for window, view in pairs(views) do
      view.lnum = Layout.reflow(previous, pages, view.lnum)
      view.topline = Layout.reflow(previous, pages, view.topline)
      vim.api.nvim_win_call(window, function()
        vim.fn.winrestview(view)
      end)
    end
  end
end

function M:visible_pages(windows)
  local visible = {}
  for _, window in ipairs(windows) do
    local view = vim.fn.getwininfo(window)[1]
    local number = Layout.page_at(self.pages, view.topline)
    while number <= #self.pages and self.pages[number].first - 1 <= view.botline do
      visible[number] = true
      number = number + 1
    end
  end
  return visible
end

function M:place(number)
  local page = self.pages[number]
  if self.failures[number] then
    vim.api.nvim_buf_set_extmark(self.buffer, namespace, page.first - 2, 0, {
      id = number,
      virt_text = { { "Unable to render page: " .. self.failures[number], "ErrorMsg" } },
    })
    return
  end
  if not self.files[number] or self.placements[number] then
    return
  end
  self.placements[number] = Snacks.image.placement.new(self.buffer, self.files[number], {
    inline = true,
    conceal = true,
    pos = { page.first, 0 },
    range = { page.first, 0, page.last, 0 },
    width = page.width,
    height = page.height,
    on_update_pre = function(placement)
      placement.opts.range[3] = page.first + placement:state().loc.height - 1
    end,
  })
end

function M:convert(number)
  self.conversion = Snacks.image.convert.convert({
    src = self.path .. "#page=" .. number,
    on_done = vim.schedule_wrap(function(conversion)
      if self.closed then
        return
      end
      self.conversion = nil
      if conversion:error() then
        self.failures[number] = tostring(conversion:error()):gsub("[\r\n]+", " ")
      else
        self.files[number] = conversion.file
      end
      self:update()
    end),
  })
  self.conversion:run()
end

function M:update()
  if self.closed then
    return
  end
  local windows = vim.tbl_filter(function(window)
    return vim.api.nvim_win_get_buf(window) == self.buffer
  end, vim.api.nvim_tabpage_list_wins(0))
  if #windows == 0 then
    self:clear_placements()
    return
  end
  self:resize(windows)
  local visible = self:visible_pages(windows)
  for number, placement in pairs(self.placements) do
    if not visible[number] then
      placement:close()
      self.placements[number] = nil
    end
  end
  local pending
  for number in pairs(visible) do
    self:place(number)
    if not self.files[number] and not self.failures[number] then
      pending = math.min(pending or number, number)
    end
  end
  if pending and not self.conversion then
    self:convert(pending)
  end
end

return M
