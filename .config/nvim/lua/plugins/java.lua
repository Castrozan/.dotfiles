return {
  {
    "mfussenegger/nvim-jdtls",
    opts = function()
      local jdtls_data_dir = vim.fn.expand("~/.cache/jdtls/workspace/" .. vim.fn.fnamemodify(vim.fn.getcwd(), ":t"))
      return {
        cmd = {
          "jdtls",
          "-configuration",
          vim.fn.expand("~/.cache/jdtls/config"),
          "-data",
          jdtls_data_dir,
        },
        root_dir = (vim.fs.root or function(_, names)
          return vim.fs.dirname(vim.fs.find(names, { upward = true })[1])
        end)(0, { ".git", "mvnw", "gradlew", "pom.xml", "build.gradle" }),
      }
    end,
  },
}
