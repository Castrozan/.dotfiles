local java_build_file_markers = {
  "settings.gradle",
  "settings.gradle.kts",
  "build.gradle",
  "build.gradle.kts",
  "pom.xml",
  "mvnw",
  "gradlew",
}

local directories_the_java_server_must_not_import = {
  "**/node_modules/**",
  "**/.metadata/**",
  "**/archetype-resources/**",
  "**/META-INF/maven/**",
  "**/.git/**",
  "**/.devenv/**",
  "**/.direnv/**",
  "**/.venv/**",
  "**/result/**",
}

return {
  {
    "mfussenegger/nvim-jdtls",
    opts = function(_, opts)
      opts.cmd = { "jdtls" }
      opts.root_dir = function(buffer_file_name)
        local directory_holding_the_file = buffer_file_name ~= "" and vim.fs.dirname(buffer_file_name) or vim.uv.cwd()
        return vim.fs.root(directory_holding_the_file, java_build_file_markers) or directory_holding_the_file
      end
      opts.settings = vim.tbl_deep_extend("force", opts.settings or {}, {
        java = { import = { exclusions = directories_the_java_server_must_not_import } },
      })
      return opts
    end,
  },
}
