use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

use anyhow::{Context, Result, bail};
use chrono::Utc;
use serde_json::json;

use claude_usage_collector::collector::{CollectorEnvironment, collect_usage_snapshot};
use claude_usage_collector::ingestion::{IngestionClient, IngestionConnection};
use claude_usage_collector::pricing::PricingTable;
use claude_usage_collector::snapshot::UsageSnapshot;

const USAGE: &str =
    "usage: claude-usage-collector <publish|snapshot> --pricing-file <litellm-prices.json>";
const CLAUDE_USAGE_TOPIC: &str = "claude-usage";
const CLAUDE_USAGE_SCHEMA_VERSION: u64 = 1;
const DEFAULT_PRODUCER_LABEL: &str = "dotfiles-usage-exporter";
const RAW_ARTIFACT_CONTENT_TYPE: &str = "application/json";
const NO_USAGE_MESSAGE: &str = "this machine recorded no usage to publish";

enum Command {
    Publish,
    Snapshot,
}

struct CommandLine {
    command: Command,
    pricing_file: PathBuf,
}

impl Command {
    fn named(name: Option<String>) -> Result<Self> {
        match name.as_deref() {
            Some("publish") => Ok(Self::Publish),
            Some("snapshot") => Ok(Self::Snapshot),
            _ => bail!(USAGE),
        }
    }

    fn execute(&self, environment: &CollectorEnvironment, pricing: &PricingTable) -> Result<()> {
        match self {
            Self::Snapshot => print_snapshot(environment, pricing),
            Self::Publish => publish_snapshot(environment, pricing),
        }
    }
}

impl CommandLine {
    fn parse(mut arguments: impl Iterator<Item = String>) -> Result<Self> {
        Ok(Self {
            command: Command::named(arguments.next())?,
            pricing_file: pricing_file_argument(arguments)?,
        })
    }
}

fn pricing_file_argument(mut arguments: impl Iterator<Item = String>) -> Result<PathBuf> {
    match (
        arguments.next().as_deref(),
        arguments.next(),
        arguments.next(),
    ) {
        (Some("--pricing-file"), Some(pricing_file), None) => Ok(PathBuf::from(pricing_file)),
        _ => bail!(USAGE),
    }
}

fn main() -> ExitCode {
    match run() {
        Ok(()) => ExitCode::SUCCESS,
        Err(failure) => {
            eprintln!("{failure:#}");
            ExitCode::FAILURE
        }
    }
}

fn run() -> Result<()> {
    let command_line = CommandLine::parse(std::env::args().skip(1))?;
    let pricing = load_pricing(&command_line.pricing_file)?;
    let environment = CollectorEnvironment::from_process()?;
    command_line.command.execute(&environment, &pricing)
}

fn load_pricing(pricing_file: &Path) -> Result<PricingTable> {
    let pricing_document = std::fs::read(pricing_file)
        .with_context(|| format!("could not read {}", pricing_file.display()))?;
    PricingTable::from_litellm_document(&pricing_document)
}

fn print_snapshot(environment: &CollectorEnvironment, pricing: &PricingTable) -> Result<()> {
    match collect_usage_snapshot(environment, pricing)? {
        Some(snapshot) => std::io::stdout().write_all(&snapshot.encoded_raw_document())?,
        None => eprintln!("{NO_USAGE_MESSAGE}"),
    }
    Ok(())
}

fn publish_snapshot(environment: &CollectorEnvironment, pricing: &PricingTable) -> Result<()> {
    let client = ingestion_client()?;
    match collect_usage_snapshot(environment, pricing)? {
        Some(snapshot) => publish_usage(&client, &snapshot),
        None => {
            println!("{NO_USAGE_MESSAGE}");
            Ok(())
        }
    }
}

fn publish_usage(client: &IngestionClient, snapshot: &UsageSnapshot) -> Result<()> {
    let produced_at = Utc::now().format("%Y-%m-%dT%H:%M:%S%.3fZ").to_string();
    let snapshot_acknowledgement = client.publish_event(
        CLAUDE_USAGE_TOPIC,
        CLAUDE_USAGE_SCHEMA_VERSION,
        snapshot.ingestion_payload()?,
        &produced_at,
    )?;
    let artifact_acknowledgement = client.put_artifact(
        &snapshot.raw_object_key(),
        RAW_ARTIFACT_CONTENT_TYPE,
        &snapshot.encoded_raw_document(),
    )?;
    println!(
        "{}",
        json!({"snapshot": snapshot_acknowledgement, "artifact": artifact_acknowledgement})
    );
    Ok(())
}

fn ingestion_client() -> Result<IngestionClient> {
    IngestionClient::new(connection_from_environment()?)
}

fn connection_from_environment() -> Result<IngestionConnection> {
    let required = |name: &str, purpose: &str| {
        std::env::var(name)
            .ok()
            .filter(|value| !value.is_empty())
            .with_context(|| format!("{name} must {purpose}"))
    };
    Ok(IngestionConnection {
        base_url: required(
            "INGEST_BASE_URL",
            "name the ingest api mount the event is sent to",
        )?,
        producer_secret: required(
            "INGEST_PRODUCER_SECRET",
            "carry the secret the ingest api accepts producers by",
        )?,
        producer_label: std::env::var("INGEST_PRODUCER_LABEL")
            .ok()
            .filter(|label| !label.is_empty())
            .unwrap_or_else(|| DEFAULT_PRODUCER_LABEL.to_string()),
    })
}
