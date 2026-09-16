import json

import pytest


@pytest.fixture
def pdf_viewer_prelude(neovim_lua_path, neovim_lua_directory, tmp_path):
    document_path = tmp_path / "report with 'quotes'.PDF"
    document_path.write_bytes(b"%PDF-1.7\noriginal bytes\n")
    return f"""
    package.path = {json.dumps(str(neovim_lua_directory / "?.lua"))} .. ";" .. package.path
    local document_path = {json.dumps(str(document_path))}
    local metadata_requests, conversions, placements = {{}}, {{}}, {{}}
    local terminal_supported, closed_placements, killed_processes, aborted_conversions = true, 0, 0, 0
    vim.fn.executable = function() return 1 end
    vim.system = function(arguments, options, callback)
      table.insert(metadata_requests, {{ arguments = arguments, options = options, callback = callback }})
      return {{ kill = function() killed_processes = killed_processes + 1 end }}
    end
    Snacks = {{ image = {{
      config = {{ wo = {{ wrap = false, number = false, relativenumber = false, signcolumn = "no" }} }},
      terminal = {{
        detect = function(callback) callback() end,
        env = function() return {{ placeholders = true }} end,
        size = function() return {{ cell_width = 10, cell_height = 20 }} end,
      }},
      supports_terminal = function() return terminal_supported end,
      util = {{ fit = function(_, bounds, options)
        local size = options.info.size
        local width = math.min(bounds.width, size.width / 12)
        return {{ width = width, height = math.min(bounds.height, math.ceil(width * size.height / size.width / 2)) }}
      end }},
      convert = {{ convert = function(options)
        local conversion = {{ file = options.src .. ".png", options = options }}
        conversion.run = function() end
        conversion.abort = function() aborted_conversions = aborted_conversions + 1 end
        conversion.error = function() return conversion.failure end
        table.insert(conversions, conversion)
        return conversion
      end }},
      placement = {{ new = function(buffer, source, options)
        local placement = {{ buffer = buffer, source = source, opts = options }}
        placement.close = function() closed_placements = closed_placements + 1; placement.closed = true end
        table.insert(placements, placement)
        return placement
      end }},
    }} }}
    local function settle()
      vim.wait(60, function() return false end, 10)
    end
    local function refresh()
      vim.cmd.redraw()
      vim.api.nvim_exec_autocmds("WinScrolled", {{}})
      settle()
    end
    local function metadata(count)
      local lines = {{ "Pages: " .. count }}
      for number = 1, count do
        table.insert(lines, "Page " .. number .. " size: 480 x 640 pts")
        table.insert(lines, "Page " .. number .. " rot: 0")
      end
      return table.concat(lines, "\\n")
    end
    local function complete_metadata(index, stdout, code, stderr)
      metadata_requests[index].callback({{ code = code or 0, stdout = stdout or metadata(3), stderr = stderr or "" }})
      settle()
      refresh()
    end
    local function complete_conversion(index, failure)
      conversions[index].failure = failure
      conversions[index].options.on_done(conversions[index])
      settle()
      refresh()
    end
    dofile({json.dumps(str(neovim_lua_path("config", "pdf", "viewer.lua")))}).setup()
    """
