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
    let document: Value =
        serde_json::from_slice(&std::fs::read(claude_account_config_path).ok()?).ok()?;
    document
        .get("oauthAccount")?
        .get("accountUuid")?
        .as_str()
        .filter(|account_uuid| !account_uuid.is_empty())
        .map(str::to_string)
}
