-- jdtls turns its root directory into a single Eclipse project, so the root decides
-- whether the import succeeds at all. Rooting a maven submodule at its own pom.xml
-- leaves the sibling modules of the reactor outside the workspace, their artifacts
-- never resolve, and the import dies before it configures the java nature: the
-- project keeps only maven2Nature, writes no .classpath, and every request fails with
-- "<module> does not exist". Rooting at the git root instead collapses unrelated loose
-- files into one project, where duplicate types poison the compile. No single marker
-- separates a reactor root from a submodule, so maven walks the unbroken chain of
-- pom.xml parents and takes the outermost one.

local gradle_reactor_root_markers = {
  "settings.gradle",
  "settings.gradle.kts",
  "gradlew",
}

local gradle_module_build_file_markers = {
  "build.gradle",
  "build.gradle.kts",
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

-- jdtls runs on jdk21 and compiles every project with it unless a matching runtime is
-- registered, so a project pinned to source and target 1.8 reports errors its own build never
-- sees. The nix module exports the java 8 home this points at.
local function java_runtimes()
  local java_eight_home = vim.env.JAVA_8_HOME
  if not java_eight_home or java_eight_home == "" then
    return nil
  end
  return { { name = "JavaSE-1.8", path = java_eight_home } }
end

local function maven_reactor_root(directory_holding_the_file)
  local outermost_directory_holding_a_pom = nil
  local directory = directory_holding_the_file
  while directory do
    if vim.uv.fs_stat(vim.fs.joinpath(directory, "pom.xml")) then
      outermost_directory_holding_a_pom = directory
    elseif outermost_directory_holding_a_pom then
      break
    end
    local parent_directory = vim.fs.dirname(directory)
    if parent_directory == directory then
      break
    end
    directory = parent_directory
  end
  return outermost_directory_holding_a_pom
end

return {
  {
    "mfussenegger/nvim-jdtls",
    opts = function(_, opts)
      opts.cmd = { "jdtls" }
      opts.root_dir = function(buffer_file_name)
        local directory_holding_the_file = buffer_file_name ~= "" and vim.fs.dirname(buffer_file_name) or vim.uv.cwd()
        return vim.fs.root(directory_holding_the_file, gradle_reactor_root_markers)
          or maven_reactor_root(directory_holding_the_file)
          or vim.fs.root(directory_holding_the_file, gradle_module_build_file_markers)
          or directory_holding_the_file
      end
      opts.settings = vim.tbl_deep_extend("force", opts.settings or {}, {
        java = {
          import = { exclusions = directories_the_java_server_must_not_import },
          configuration = { runtimes = java_runtimes() },
        },
      })
      return opts
    end,
  },
}
