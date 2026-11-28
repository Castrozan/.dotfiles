use std::fs::OpenOptions;
use std::io::Write;
use std::path::{Path, PathBuf};

use claude_usage_collector::ledger::UsageLedger;
use claude_usage_collector::pricing::PricingTable;
use claude_usage_collector::usage_totals::DailyModelUsage;

pub const PRICING_DOCUMENT: &str = r#"{
    "claude-opus-5-5": {"input_cost_per_token": 4e-6, "output_cost_per_token": 2e-5},
    "claude-haiku-5-5": {"input_cost_per_token": 1e-7, "output_cost_per_token": 5e-7}
}"#;

#[derive(Debug, Clone)]
pub struct SampleUsage {
    pub message: u8,
    pub request: Option<u8>,
    pub is_sidechain: bool,
    pub day: u8,
    pub model: &'static str,
    pub input: u32,
    pub output: u32,
}

impl SampleUsage {
    pub fn line(&self) -> String {
        let request = self.request.map_or(String::new(), |request| {
            format!(r#""requestId":"req_{request}","#)
        });
        format!(
            r#"{{"type":"assistant","timestamp":"2026-11-{:02}T12:00:00.000Z",{request}"isSidechain":{},"message":{{"id":"msg_{}","model":"{}","usage":{{"input_tokens":{},"output_tokens":{}}}}}}}"#,
            10 + self.day,
            self.is_sidechain,
            self.message,
            self.model,
            self.input,
            self.output
        )
    }
}

pub fn pricing() -> PricingTable {
    PricingTable::from_litellm_document(PRICING_DOCUMENT.as_bytes()).unwrap()
}

pub fn append_lines(path: &Path, lines: &[String]) {
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .unwrap();
    for line in lines {
        writeln!(file, "{line}").unwrap();
    }
}

pub fn ingest(ledger_path: &Path, transcripts: &[PathBuf], pricing: &PricingTable) -> u64 {
    let mut ledger = UsageLedger::open(ledger_path).unwrap();
    ledger.reconcile_pricing(pricing).unwrap();
    ledger
        .ingest_transcripts(transcripts, pricing)
        .unwrap()
        .recorded_entries
}

pub fn report(ledger_path: &Path) -> Vec<DailyModelUsage> {
    UsageLedger::open(ledger_path)
        .unwrap()
        .daily_model_usage()
        .unwrap()
}
