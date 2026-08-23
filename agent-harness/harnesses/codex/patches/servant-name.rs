use sha2::Digest;
use sha2::Sha256;

const SERVANT_ROSTER: &str = include_str!(env!("CODEX_SERVANT_ROSTER_PATH"));

pub(crate) fn select_servant_name(session_id: &str) -> Option<&'static str> {
    SERVANT_ROSTER
        .lines()
        .filter_map(|line| line.split_once('|').map(|(name, _)| name.trim()))
        .filter(|name| !name.is_empty())
        .max_by_key(|name| {
            let mut digest = Sha256::new();
            digest.update(session_id.as_bytes());
            digest.update([0]);
            digest.update(name.as_bytes());
            digest.finalize()
        })
}

#[cfg(test)]
mod tests {
    use super::select_servant_name;

    #[test]
    fn matches_the_shared_catalog_draw() {
        assert_eq!(
            select_servant_name("statusline-probe"),
            Some("Jeanne d'Arc (Alter)")
        );
    }
}
