local file_creation = {}

local function directory_holding_the_current_buffer()
  local current_file_path = vim.api.nvim_buf_get_name(0)
  if current_file_path == "" or vim.bo.buftype ~= "" then
    return vim.fn.getcwd()
  end
  return vim.fs.dirname(current_file_path)
end

local function create_empty_file(new_file_path)
  local new_file_handle = assert(io.open(new_file_path, "w"))
  new_file_handle:close()
end

local function create_and_open(target_directory, typed_name)
  local new_file_path = vim.fs.normalize(target_directory .. "/" .. typed_name)
  if vim.uv.fs_stat(new_file_path) then
    vim.notify(new_file_path .. " already exists", vim.log.levels.WARN)
    return
  end
  vim.fn.mkdir(vim.fs.dirname(new_file_path), "p")
  create_empty_file(new_file_path)
  vim.cmd.edit(vim.fn.fnameescape(new_file_path))
end

function file_creation.create()
  local target_directory = directory_holding_the_current_buffer()
  vim.ui.input({ prompt = "New file in " .. target_directory .. "/" }, function(typed_name)
    if not typed_name or typed_name:match("^%s*$") then
      return
    end
    create_and_open(target_directory, typed_name)
  end)
end

return file_creation
