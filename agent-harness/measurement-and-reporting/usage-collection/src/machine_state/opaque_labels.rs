use std::path::Path;

use serde_json::Value;
use sha2::{Digest, Sha256};

const ACCOUNT_LABEL_NAMESPACE: &str = "dotfiles-usage-account-v1";
const MACHINE_LABEL_NAMESPACE: &str = "dotfiles-usage-machine-v1";
const OPAQUE_LABEL_LENGTH: usize = 12;

fn opaque_label(label_namespace: &str, raw_identifier: &str) -> String {
    let digest = Sha256::digest(format!("{label_namespace}:{raw_identifier}").as_bytes());
    let mut hexadecimal = format!("{digest:x}");
    hexadecimal.truncate(OPAQUE_LABEL_LENGTH);
    hexadecimal
}

pub fn account_label(account_uuid: &str) -> String {
    opaque_label(ACCOUNT_LABEL_NAMESPACE, account_uuid)
}

pub fn machine_label(machine_hostname: &str) -> String {
    opaque_label(MACHINE_LABEL_NAMESPACE, machine_hostname)
}

pub fn current_account_uuid(claude_account_config_path: &Path) -> Option<String> {
    let document = read_json_document(claude_account_config_path)?;
    let account_uuid = document.pointer("/oauthAccount/accountUuid")?.as_str()?;
    (!account_uuid.is_empty()).then(|| account_uuid.to_string())
}

fn read_json_document(path: &Path) -> Option<Value> {
    let bytes = std::fs::read(path).ok()?;
    serde_json::from_slice(&bytes).ok()
}
