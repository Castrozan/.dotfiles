use std::collections::BTreeSet;
use std::path::PathBuf;
use std::time::Instant;

use anyhow::{Context, Result};
use chrono::Utc;

use crate::ledger::UsageLedger;
use crate::machine_state::{
    account_label, current_account_uuid, machine_label, read_stats_cache_summary,
    summarize_otel_metrics_file,
};
use crate::pricing::PricingTable;
use crate::snapshot::UsageSnapshot;
use crate::transcript::{ClaudeDataLocations, transcript_files};

const LEDGER_DIRECTORY: &str = "claude-usage-collector";
const LEDGER_FILE: &str = "ledger.sqlite3";

pub struct CollectorEnvironment {
    pub home: PathBuf,
    pub state_home: Option<PathBuf>,
    pub claude_config_dir: Option<String>,
    pub xdg_config_home: Option<PathBuf>,
    pub hostname: String,
}

impl CollectorEnvironment {
    pub fn from_process() -> Result<Self> {
        let non_empty = |name: &str| std::env::var(name).ok().filter(|value| !value.is_empty());
        Ok(Self {
            home: non_empty("HOME")
                .map(PathBuf::from)
                .context("HOME must name the user's home directory")?,
            state_home: non_empty("XDG_STATE_HOME").map(PathBuf::from),
            claude_config_dir: non_empty("CLAUDE_CONFIG_DIR"),
            xdg_config_home: non_empty("XDG_CONFIG_HOME").map(PathBuf::from),
            hostname: gethostname::gethostname().to_string_lossy().into_owned(),
        })
    }

    pub fn ledger_path(&self) -> PathBuf {
        self.state_home
            .clone()
            .unwrap_or_else(|| self.home.join(".local").join("state"))
            .join(LEDGER_DIRECTORY)
            .join(LEDGER_FILE)
    }

    fn claude_home(&self) -> PathBuf {
        self.home.join(".claude")
    }
}

pub fn collect_usage_snapshot(
    environment: &CollectorEnvironment,
    pricing: &PricingTable,
) -> Result<Option<UsageSnapshot>> {
    let Some(account_uuid) = current_account_uuid(&environment.home.join(".claude.json")) else {
        return Ok(None);
    };
    let data_directories = ClaudeDataLocations {
        home: &environment.home,
        claude_config_dir: environment.claude_config_dir.as_deref(),
        xdg_config_home: environment.xdg_config_home.as_deref(),
    }
    .data_directories()?;
    let transcripts = transcript_files(&data_directories);
    let mut ledger = UsageLedger::open(&environment.ledger_path())?;
    ledger.reconcile_pricing(pricing)?;
    let ingestion_started = Instant::now();
    let ingestion = ledger.ingest_transcripts(&transcripts, pricing)?;
    eprintln!(
        "recorded {} usage entries from {} changed of {} transcripts in {:.2}s",
        ingestion.recorded_entries,
        ingestion.changed_transcripts,
        transcripts.len(),
        ingestion_started.elapsed().as_secs_f64()
    );
    let daily_model_usage = ledger.daily_model_usage()?;
    report_unpriced_models(&daily_model_usage, pricing);
    if daily_model_usage.is_empty() {
        return Ok(None);
    }
    Ok(Some(UsageSnapshot {
        account_label: account_label(&account_uuid),
        machine_label: machine_label(&environment.hostname),
        captured_at_utc: Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string(),
        stats_cache: read_stats_cache_summary(&environment.claude_home().join("stats-cache.json")),
        daily_model_usage,
        otel_metrics: summarize_otel_metrics_file(
            &environment
                .claude_home()
                .join("otel-metrics")
                .join("metrics.jsonl"),
        ),
    }))
}

fn report_unpriced_models(
    daily_model_usage: &[crate::usage_totals::DailyModelUsage],
    pricing: &PricingTable,
) {
    let unpriced_models: BTreeSet<&str> = daily_model_usage
        .iter()
        .filter(|usage| usage.totals.token_total() > 0 && pricing.price_for(&usage.model).is_none())
        .map(|usage| usage.model.as_str())
        .collect();
    if !unpriced_models.is_empty() {
        eprintln!(
            "no LiteLLM price for {}; their cost counts as zero",
            unpriced_models.into_iter().collect::<Vec<_>>().join(", ")
        );
    }
}
