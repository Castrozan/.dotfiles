def test_every_page_is_in_one_read_only_buffer_with_native_scrolling(
    run_headless_lua, pdf_viewer_prelude
):
    result = run_headless_lua(
        "pdf_continuous_scroll.lua",
        pdf_viewer_prelude
        + """
        vim.cmd.edit(document_path)
        complete_metadata(1)
        assert(metadata_requests[1].arguments[6] == document_path)
        assert(metadata_requests[1].options.timeout == 10000)
        local lines = vim.api.nvim_buf_get_lines(0, 0, -1, false)
        assert(lines[1] == "Page 1 / 3")
        assert(vim.tbl_contains(lines, "Page 2 / 3") and vim.tbl_contains(lines, "Page 3 / 3"))
        assert(#lines > 100, "pages have no real buffer rows to scroll through")
        complete_conversion(1)
        assert(placements[1].opts.inline and placements[1].opts.range[3] > placements[1].opts.range[1])
        vim.cmd("normal! G")
        refresh()
        assert(vim.fn.line(".") == #lines)
        assert(conversions[2].options.src == document_path .. "#page=3")
        complete_conversion(2)
        vim.cmd("normal! gg")
        refresh()
        assert(#conversions == 2, "returning to a converted page rendered the PDF again")
        assert(vim.fn.line(".") == 1)
        assert(not pcall(vim.cmd, "write!"))
        assert(vim.fn.readfile(document_path)[2] == "original bytes")
        assert(not vim.api.nvim_exec2("messages", { output = true }).output:find("W10", 1, true))
        assert(vim.fn.exists(":PdfPage") == 0)
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_rapid_scrolling_prioritizes_the_visible_page_with_one_conversion(
    run_headless_lua, pdf_viewer_prelude
):
    result = run_headless_lua(
        "pdf_scroll_work_bound.lua",
        pdf_viewer_prelude
        + """
        vim.cmd.edit(document_path)
        complete_metadata(1, metadata(300))
        for number = 1, 50 do
          vim.api.nvim_win_set_cursor(0, { number * 30, 0 })
          refresh()
        end
        vim.cmd("normal! G")
        refresh()
        assert(#conversions == 1, "scroll events queued conversions while one was running")
        complete_conversion(1)
        assert(#conversions == 2)
        assert(conversions[2].options.src == document_path .. "#page=300")
        assert(#placements == 0, "an offscreen page was placed after its conversion finished")
        complete_conversion(2)
        assert(#placements == 1)
        assert(placements[1].source:find("#page=300", 1, true))
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_resize_preserves_the_page_and_offscreen_images_are_released(
    run_headless_lua, pdf_viewer_prelude
):
    result = run_headless_lua(
        "pdf_resize.lua",
        pdf_viewer_prelude
        + """
        vim.cmd.edit(document_path)
        complete_metadata(1)
        complete_conversion(1)
        vim.cmd("normal! G")
        refresh()
        assert(closed_placements == 1)
        complete_conversion(2)
        local lines = vim.api.nvim_buf_get_lines(0, 0, -1, false)
        for number, line in ipairs(lines) do
          if line == "Page 3 / 3" then vim.api.nvim_win_set_cursor(0, { number, 0 }) end
        end
        vim.cmd.vsplit()
        vim.api.nvim_win_set_width(0, 25)
        vim.api.nvim_exec_autocmds("WinResized", {})
        settle()
        assert(vim.api.nvim_get_current_line() == "Page 3 / 3", "resizing moved to a different page")
        assert(vim.api.nvim_buf_line_count(0) < #lines)
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_mixed_page_sizes_and_rotations_determine_the_scrolling_layout(
    run_headless_lua, pdf_viewer_prelude
):
    result = run_headless_lua(
        "pdf_page_dimensions.lua",
        pdf_viewer_prelude
        + """
        local layout = require("config.pdf.page_layout")
        local sizes = layout.parse([[Pages: 3
Page 1 size: 480 x 640 pts
Page 1 rot: 0
Page 2 size: 640 x 480 pts
Page 2 rot: 0
Page 3 size: 480 x 640 pts
Page 3 rot: 90]])
        assert(sizes[1].height > sizes[2].height)
        assert(sizes[2].width == sizes[3].width and sizes[2].height == sizes[3].height)
        local pages, lines = layout.build({ { width = 80, height = 54 }, { width = 80, height = 30 } })
        assert(pages[2].first == 58 and #lines == 88)
        assert(pages[2].first > pages[1].last)
        assert(layout.parse("Pages: 1\\nPage 1 size: 0 x 640 pts") == nil)
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_hidden_tabs_release_images_and_do_not_convert_more_pages(
    run_headless_lua, pdf_viewer_prelude
):
    result = run_headless_lua(
        "pdf_hidden_tab.lua",
        pdf_viewer_prelude
        + """
        vim.cmd.edit(document_path)
        complete_metadata(1)
        complete_conversion(1)
        vim.cmd("normal! G")
        refresh()
        assert(#conversions == 2)
        vim.cmd.tabnew()
        settle()
        complete_conversion(2)
        assert(#placements == 1 and closed_placements == 1)
        vim.cmd.tabprevious()
        settle()
        assert(#placements == 2 and #conversions == 2)
        assert(placements[2].source:find("#page=3", 1, true))
        vim.cmd("qa!")
        """,
    )
    assert result.returncode == 0, result.stdout + result.stderr
