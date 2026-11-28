use std::path::{Path, PathBuf};

use anyhow::{Result, bail};
use walkdir::WalkDir;

const PROJECTS_DIRECTORY: &str = "projects";
const TRANSCRIPT_EXTENSION: &str = "jsonl";

pub struct ClaudeDataLocations<'a> {
    pub home: &'a Path,
    pub claude_config_dir: Option<&'a str>,
    pub xdg_config_home: Option<&'a Path>,
}

impl ClaudeDataLocations<'_> {
    pub fn data_directories(&self) -> Result<Vec<PathBuf>> {
        match self.configured_list() {
            None => Ok(unique_directories_with_projects(self.default_directories())),
            Some(configured_list) => self.configured_directories(configured_list),
        }
    }

    fn configured_list(&self) -> Option<&str> {
        self.claude_config_dir
            .filter(|list| !list.trim().is_empty())
    }

    fn configured_directories(&self, configured_list: &str) -> Result<Vec<PathBuf>> {
        let configured = unique_directories_with_projects(
            configured_list
                .split(',')
                .map(str::trim)
                .filter(|part| !part.is_empty())
                .map(|part| data_directory_for(self.expand_home(part))),
        );
        if configured.is_empty() {
            bail!(
                "CLAUDE_CONFIG_DIR names no directory holding a projects folder: {configured_list}"
            );
        }
        Ok(configured)
    }

    fn default_directories(&self) -> Vec<PathBuf> {
        let config_home = self
            .xdg_config_home
            .map(Path::to_path_buf)
            .unwrap_or_else(|| self.home.join(".config"));
        vec![config_home.join("claude"), self.home.join(".claude")]
    }

    fn expand_home(&self, part: &str) -> PathBuf {
        match part.strip_prefix('~') {
            Some("") => self.home.to_path_buf(),
            Some(rest) if rest.starts_with('/') => self.home.join(rest.trim_start_matches('/')),
            _ => PathBuf::from(part),
        }
    }
}

fn data_directory_for(path: PathBuf) -> PathBuf {
    if path
        .file_name()
        .is_some_and(|name| name == PROJECTS_DIRECTORY)
        && let Some(parent) = path.parent()
    {
        return parent.to_path_buf();
    }
    path
}

fn unique_directories_with_projects(candidates: impl IntoIterator<Item = PathBuf>) -> Vec<PathBuf> {
    let mut directories: Vec<PathBuf> = Vec::new();
    for candidate in candidates {
        if candidate.join(PROJECTS_DIRECTORY).is_dir() && !directories.contains(&candidate) {
            directories.push(candidate);
        }
    }
    directories
}

pub fn transcript_files(data_directories: &[PathBuf]) -> Vec<PathBuf> {
    let mut files: Vec<PathBuf> = data_directories
        .iter()
        .flat_map(|directory| WalkDir::new(directory.join(PROJECTS_DIRECTORY)).follow_links(false))
        .filter_map(Result::ok)
        .filter(is_transcript)
        .map(walkdir::DirEntry::into_path)
        .collect();
    files.sort();
    files.dedup();
    files
}

fn is_transcript(entry: &walkdir::DirEntry) -> bool {
    entry.file_type().is_file()
        && entry
            .path()
            .extension()
            .is_some_and(|extension| extension == TRANSCRIPT_EXTENSION)
}
