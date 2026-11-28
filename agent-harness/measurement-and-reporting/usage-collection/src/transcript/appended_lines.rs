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
    let mut reader = reader_at(path, start_offset)?;
    let mut consumed_offset = start_offset;
    let mut line_bytes = Vec::new();
    while let Some(line_length) = next_complete_line(&mut reader, &mut line_bytes)? {
        consumed_offset += line_length as u64;
        if let Ok(line) = std::str::from_utf8(&line_bytes[..line_length - 1]) {
            each_line(line);
        }
    }
    Ok(consumed_offset)
}

fn reader_at(path: &Path, start_offset: u64) -> io::Result<BufReader<File>> {
    let mut file = File::open(path)?;
    file.seek(SeekFrom::Start(start_offset))?;
    Ok(BufReader::with_capacity(READ_BUFFER_BYTES, file))
}

fn next_complete_line(
    reader: &mut impl BufRead,
    line_bytes: &mut Vec<u8>,
) -> io::Result<Option<usize>> {
    line_bytes.clear();
    let read_bytes = reader.read_until(b'\n', line_bytes)?;
    Ok((line_bytes.last() == Some(&b'\n')).then_some(read_bytes))
}
