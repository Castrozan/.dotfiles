use std::fs::File;
use std::io::{self, BufRead, BufReader, Seek, SeekFrom};
use std::os::unix::fs::MetadataExt;
use std::path::Path;

const READ_BUFFER_BYTES: usize = 1 << 20;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct FileIdentity {
    pub device: u64,
    pub inode: u64,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct TranscriptFileState {
    pub identity: FileIdentity,
    pub length: u64,
}

pub fn transcript_file_state(path: &Path) -> io::Result<TranscriptFileState> {
    let metadata = std::fs::metadata(path)?;
    Ok(TranscriptFileState {
        identity: FileIdentity {
            device: metadata.dev(),
            inode: metadata.ino(),
        },
        length: metadata.len(),
    })
}

pub fn read_complete_lines_from(
    path: &Path,
    start_offset: u64,
    mut each_line: impl FnMut(&str),
) -> io::Result<u64> {
    let mut file = File::open(path)?;
    file.seek(SeekFrom::Start(start_offset))?;
    let mut reader = BufReader::with_capacity(READ_BUFFER_BYTES, file);
    let mut consumed_offset = start_offset;
    let mut line_bytes = Vec::new();
    loop {
        line_bytes.clear();
        let read_bytes = reader.read_until(b'\n', &mut line_bytes)?;
        if read_bytes == 0 || line_bytes.last() != Some(&b'\n') {
            return Ok(consumed_offset);
        }
        consumed_offset += read_bytes as u64;
        if let Ok(line) = std::str::from_utf8(&line_bytes[..read_bytes - 1]) {
            each_line(line);
        }
    }
}
