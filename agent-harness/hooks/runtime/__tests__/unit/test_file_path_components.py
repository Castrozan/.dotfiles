"""Splitting a path into its parts without paying for pathlib.

The routers that ask whether an edited file sits under a skills, docs or
node_modules directory run on every Edit, and pathlib.PurePath.parts costs
urllib.parse, ipaddress and fnmatch to answer it. These cover the shapes where
a naive split on the separator disagrees with what pathlib returns.
"""

from file_path_components import path_components


def test_an_absolute_path_drops_the_empty_leading_component():
    assert path_components("/a/b/c.md") == ["a", "b", "c.md"]


def test_a_relative_path_keeps_every_component():
    assert path_components("a/b/c.md") == ["a", "b", "c.md"]


def test_repeated_and_trailing_separators_produce_no_empty_components():
    assert path_components("//a//b//") == ["a", "b"]


def test_an_empty_path_has_no_components():
    assert path_components("") == []


def test_a_bare_filename_is_its_own_only_component():
    assert path_components("CLAUDE.md") == ["CLAUDE.md"]
