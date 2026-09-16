local M = {}

function M.parse(metadata)
  local count = tonumber(metadata:match("Pages:%s+(%d+)"))
  if not count or count < 1 then
    return nil
  end
  local pages = {}
  for number, width, height in metadata:gmatch("Page%s+(%d+)%s+size:%s+([%d.]+)%s+x%s+([%d.]+)") do
    pages[tonumber(number)] = { width = tonumber(width), height = tonumber(height) }
  end
  for number, rotation in metadata:gmatch("Page%s+(%d+)%s+rot:%s+([%-]?%d+)") do
    local page = pages[tonumber(number)]
    if page and tonumber(rotation) % 180 ~= 0 then
      page.width, page.height = page.height, page.width
    end
  end
  for number = 1, count do
    local page = pages[number]
    if not page or page.width <= 0 or page.height <= 0 then
      return nil
    end
  end
  return pages
end

function M.build(sizes)
  local pages, lines = {}, {}
  for number, size in ipairs(sizes) do
    local height = size.height
    lines[#lines + 1] = string.format("Page %d / %d", number, #sizes)
    local first = #lines + 1
    for _ = 1, height do
      lines[#lines + 1] = ""
    end
    pages[number] = { first = first, last = #lines, width = size.width, height = height }
    lines[#lines + 1] = ""
  end
  return pages, lines
end

function M.page_at(pages, line)
  local first, last = 1, #pages
  while first < last do
    local middle = math.ceil((first + last) / 2)
    if pages[middle].first - 1 <= line then
      first = middle
    else
      last = middle - 1
    end
  end
  return first
end

function M.reflow(previous, current, line)
  local number = M.page_at(previous, line)
  local offset = math.max(0, line - previous[number].first + 1)
  local fraction = offset / (previous[number].height + 2)
  return current[number].first - 1 + math.floor(fraction * (current[number].height + 2))
end

return M
