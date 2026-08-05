local java_project_root_markers = {
  "settings.gradle",
  "settings.gradle.kts",
  "build.gradle",
  "build.gradle.kts",
  "pom.xml",
  "mvnw",
  "gradlew",
  ".git",
}

return {
  {
    "mfussenegger/nvim-jdtls",
    opts = function(_, opts)
      opts.cmd = { "jdtls" }
      opts.root_dir = function(buffer_file_name)
        local search_start_path = buffer_file_name ~= "" and buffer_file_name or vim.uv.cwd()
        return vim.fs.root(search_start_path, java_project_root_markers)
      end
      return opts
    end,
  },
}
