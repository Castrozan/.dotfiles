import QtQuick
import QtTest

Item {
    id: root

    QtObject {
        id: launcherWallpapersService

        property var availableWallpapers: []

        function search(queryText) {
            var lowerQuery = queryText.toLowerCase();
            return availableWallpapers.filter(function(wallpaper) {
                return wallpaper.name.toLowerCase().includes(lowerQuery);
            });
        }

        function parseWallpaperListOutput(output) {
            var wallpapers = [];
            var lines = output.split("\n");
            for (var i = 0; i < lines.length; i++) {
                var trimmedPath = lines[i].trim();
                if (trimmedPath.length === 0)
                    continue;
                var lastSlashIndex = trimmedPath.lastIndexOf("/");
                var fileName = lastSlashIndex >= 0 ? trimmedPath.substring(lastSlashIndex + 1) : trimmedPath;
                wallpapers.push({
                    name: fileName,
                    path: trimmedPath
                });
            }
            wallpapers.sort(function(wallpaperA, wallpaperB) {
                return wallpaperA.name.localeCompare(wallpaperB.name);
            });
            availableWallpapers = wallpapers;
        }
    }

    TestCase {
        name: "LauncherWallpapersServiceParseOutput"

        function init() {
            launcherWallpapersService.availableWallpapers = [];
        }

        function test_parses_single_wallpaper_path() {
            launcherWallpapersService.parseWallpaperListOutput("/home/user/wallpapers/sunset.jpg\n");
            compare(launcherWallpapersService.availableWallpapers.length, 1);
            compare(launcherWallpapersService.availableWallpapers[0].name, "sunset.jpg");
            compare(launcherWallpapersService.availableWallpapers[0].path, "/home/user/wallpapers/sunset.jpg");
        }

        function test_parses_multiple_wallpaper_paths() {
            var output = "/home/user/wallpapers/forest.png\n/home/user/wallpapers/ocean.jpg\n/home/user/wallpapers/alpine.webp\n";
            launcherWallpapersService.parseWallpaperListOutput(output);
            compare(launcherWallpapersService.availableWallpapers.length, 3);
        }

        function test_sorts_wallpapers_alphabetically_by_name() {
            var output = "/wall/zebra.png\n/wall/alpine.jpg\n/wall/mountain.webp\n";
            launcherWallpapersService.parseWallpaperListOutput(output);
            compare(launcherWallpapersService.availableWallpapers[0].name, "alpine.jpg");
            compare(launcherWallpapersService.availableWallpapers[1].name, "mountain.webp");
            compare(launcherWallpapersService.availableWallpapers[2].name, "zebra.png");
        }

        function test_skips_empty_lines() {
            var output = "/wall/test.jpg\n\n\n/wall/other.png\n\n";
            launcherWallpapersService.parseWallpaperListOutput(output);
            compare(launcherWallpapersService.availableWallpapers.length, 2);
        }

        function test_handles_empty_output() {
            launcherWallpapersService.parseWallpaperListOutput("");
            compare(launcherWallpapersService.availableWallpapers.length, 0);
        }

        function test_handles_only_newlines() {
            launcherWallpapersService.parseWallpaperListOutput("\n\n\n");
            compare(launcherWallpapersService.availableWallpapers.length, 0);
        }

        function test_trims_whitespace_from_paths() {
            launcherWallpapersService.parseWallpaperListOutput("  /wall/padded.jpg  \n");
            compare(launcherWallpapersService.availableWallpapers.length, 1);
            compare(launcherWallpapersService.availableWallpapers[0].path, "/wall/padded.jpg");
        }

        function test_extracts_filename_from_path() {
            launcherWallpapersService.parseWallpaperListOutput("/deeply/nested/directory/structure/image.png\n");
            compare(launcherWallpapersService.availableWallpapers[0].name, "image.png");
        }

        function test_handles_filename_without_directory() {
            launcherWallpapersService.parseWallpaperListOutput("standalone.jpg\n");
            compare(launcherWallpapersService.availableWallpapers[0].name, "standalone.jpg");
            compare(launcherWallpapersService.availableWallpapers[0].path, "standalone.jpg");
        }

        function test_preserves_full_path_in_path_field() {
            var fullPath = "/home/user/.config/hypr-theme/wallpapers/catppuccin-mocha.png";
            launcherWallpapersService.parseWallpaperListOutput(fullPath + "\n");
            compare(launcherWallpapersService.availableWallpapers[0].path, fullPath);
        }
    }

    TestCase {
        name: "LauncherWallpapersServiceSearch"

        function init() {
            launcherWallpapersService.availableWallpapers = [
                { name: "sunset.jpg", path: "/wall/sunset.jpg" },
                { name: "forest-green.png", path: "/wall/forest-green.png" },
                { name: "ocean-blue.webp", path: "/wall/ocean-blue.webp" },
                { name: "mountain-peak.jpg", path: "/wall/mountain-peak.jpg" },
                { name: "catppuccin-mocha.png", path: "/wall/catppuccin-mocha.png" }
            ];
        }

        function test_search_matches_by_filename() {
            var results = launcherWallpapersService.search("sunset");
            compare(results.length, 1);
            compare(results[0].name, "sunset.jpg");
        }

        function test_search_is_case_insensitive() {
            var results = launcherWallpapersService.search("FOREST");
            compare(results.length, 1);
            compare(results[0].name, "forest-green.png");
        }

        function test_search_partial_match() {
            var results = launcherWallpapersService.search("mou");
            compare(results.length, 1);
            compare(results[0].name, "mountain-peak.jpg");
        }

        function test_search_returns_empty_for_no_match() {
            var results = launcherWallpapersService.search("zzzznonexistent");
            compare(results.length, 0);
        }

        function test_search_empty_query_returns_all() {
            var results = launcherWallpapersService.search("");
            compare(results.length, 5);
        }

        function test_search_matches_file_extension() {
            var results = launcherWallpapersService.search(".webp");
            compare(results.length, 1);
            compare(results[0].name, "ocean-blue.webp");
        }

        function test_search_matches_multiple_results() {
            var results = launcherWallpapersService.search(".jpg");
            compare(results.length, 2);
        }

        function test_search_with_hyphenated_name() {
            var results = launcherWallpapersService.search("catppuccin");
            compare(results.length, 1);
            compare(results[0].name, "catppuccin-mocha.png");
        }
    }
}
