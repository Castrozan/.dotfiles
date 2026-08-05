local inheritable_mapping_option_names = {
  "mode",
  "buffer",
  "silent",
  "nowait",
  "expr",
  "remap",
  "noremap",
}

local function options_inherited_by_node(node, options_from_ancestors)
  local options = vim.deepcopy(options_from_ancestors)
  for _, option_name in ipairs(inheritable_mapping_option_names) do
    if node[option_name] ~= nil then
      options[option_name] = node[option_name]
    end
  end
  return options
end

local function keymap_options_from(node, options)
  return {
    buffer = options.buffer,
    desc = node.desc,
    silent = options.silent ~= false,
    nowait = options.nowait,
    expr = options.expr,
    remap = options.remap or options.noremap == false or nil,
  }
end

local function set_mappings_from_node(node, options_from_ancestors)
  local options = options_inherited_by_node(node, options_from_ancestors)
  local left_hand_side, right_hand_side = node[1], node[2]
  if type(left_hand_side) == "string" then
    if right_hand_side ~= nil then
      vim.keymap.set(options.mode or "n", left_hand_side, right_hand_side, keymap_options_from(node, options))
    end
    return
  end
  for _, child_node in ipairs(node) do
    if type(child_node) == "table" then
      set_mappings_from_node(child_node, options)
    end
  end
end

local function add_mappings(specification)
  if type(specification) == "table" then
    set_mappings_from_node(specification, {})
  end
end

local function which_key_plugin_is_enabled()
  local lazy_configuration = package.loaded["lazy.core.config"]
  return lazy_configuration ~= nil and lazy_configuration.spec.plugins["which-key.nvim"] ~= nil
end

return {
  install = function()
    if which_key_plugin_is_enabled() then
      return
    end
    package.preload["which-key"] = function()
      return {
        add = add_mappings,
        register = add_mappings,
        setup = function() end,
        show = function() end,
      }
    end
  end,
}
