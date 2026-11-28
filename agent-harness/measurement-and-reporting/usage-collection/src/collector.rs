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
use crate::usage_totals::DailyModelUsage;

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
        Ok(Self {
            home: path_variable("HOME").context("HOME must name the user's home directory")?,
            state_home: path_variable("XDG_STATE_HOME"),
            claude_config_dir: non_empty_variable("CLAUDE_CONFIG_DIR"),
            xdg_config_home: path_variable("XDG_CONFIG_HOME"),
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

    fn transcripts(&self) -> Result<Vec<PathBuf>> {
        let data_directories = ClaudeDataLocations {
            home: &self.home,
            claude_config_dir: self.claude_config_dir.as_deref(),
            xdg_config_home: self.xdg_config_home.as_deref(),
        }
        .data_directories()?;
        Ok(transcript_files(&data_directories))
    }

    fn snapshot(
        &self,
        account_uuid: &str,
        daily_model_usage: Vec<DailyModelUsage>,
    ) -> UsageSnapshot {
        let claude_home = self.claude_home();
        UsageSnapshot {
            account_label: account_label(account_uuid),
            machine_label: machine_label(&self.hostname),
            captured_at_utc: Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string(),
            stats_cache: read_stats_cache_summary(&claude_home.join("stats-cache.json")),
            daily_model_usage,
            otel_metrics: summarize_otel_metrics_file(
                &claude_home.join("otel-metrics").join("metrics.jsonl"),
            ),
        }
    }
}

fn non_empty_variable(name: &str) -> Option<String> {
    std::env::var(name).ok().filter(|value| !value.is_empty())
}

fn path_variable(name: &str) -> Option<PathBuf> {
    non_empty_variable(name).map(PathBuf::from)
}

pub fn collect_usage_snapshot(
    environment: &CollectorEnvironment,
    pricing: &PricingTable,
) -> Result<Option<UsageSnapshot>> {
    let Some(account_uuid) = current_account_uuid(&environment.home.join(".claude.json")) else {
        return Ok(None);
    };
    let daily_model_usage = refresh_daily_model_usage(environment, pricing)?;
    if daily_model_usage.is_empty() {
        return Ok(None);
    }
    Ok(Some(environment.snapshot(&account_uuid, daily_model_usage)))
}

fn refresh_daily_model_usage(
    environment: &CollectorEnvironment,
    pricing: &PricingTable,
) -> Result<Vec<DailyModelUsage>> {
    let transcripts = environment.transcripts()?;
    let mut ledger = UsageLedger::open(&environment.ledger_path())?;
    ingest_with_report(&mut ledger, &transcripts, pricing)?;
    let daily_model_usage = ledger.daily_model_usage()?;
    report_unpriced_models(&daily_model_usage, pricing);
    Ok(daily_model_usage)
}

fn ingest_with_report(
    ledger: &mut UsageLedger,
    transcripts: &[PathBuf],
    pricing: &PricingTable,
) -> Result<()> {
    ledger.reconcile_pricing(pricing)?;
    let ingestion_started = Instant::now();
    let ingestion = ledger.ingest_transcripts(transcripts, pricing)?;
    eprintln!(
        "recorded {} usage entries from {} changed of {} transcripts in {:.2}s",
        ingestion.recorded_entries,
        ingestion.changed_transcripts,
        transcripts.len(),
        ingestion_started.elapsed().as_secs_f64()
    );
    Ok(())
}

fn report_unpriced_models(daily_model_usage: &[DailyModelUsage], pricing: &PricingTable) {
    let unpriced_models: BTreeSet<&str> = daily_model_usage
        .iter()
        .filter(|usage| usage.totals.token_total() > 0 && pricing.price_for(&usage.model).is_none())
        .map(|usage| usage.model.as_str())
        .collect();
    if unpriced_models.is_empty() {
        return;
    }
    eprintln!(
        "no LiteLLM price for {}; their cost counts as zero",
        unpriced_models.into_iter().collect::<Vec<_>>().join(", ")
    );
}
