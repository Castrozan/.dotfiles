use std::time::Duration;

use anyhow::{Result, anyhow, bail};
use percent_encoding::{AsciiSet, NON_ALPHANUMERIC, utf8_percent_encode};
use serde_json::{Map, Value, json};

use super::endpoint_policy::is_permitted_ingestion_endpoint;
use super::response::{IngestFailure, accepted_acknowledgement, exchange};

const PRODUCER_AUTHENTICATION_HEADER_NAME: &str = "x-ingest-producer-secret";
const PUBLISHER_USER_AGENT: &str = "dotfiles-ingestion-publisher/1";
const INGEST_REQUEST_TIMEOUT: Duration = Duration::from_secs(30);
const UNPERMITTED_ENDPOINT_MESSAGE: &str =
    "Ingestion requires credential-free HTTPS or explicit loopback HTTP without query or fragment";
const ARTIFACT_PUT_ATTEMPT_DELAYS: [Duration; 3] = [
    Duration::ZERO,
    Duration::from_secs(2),
    Duration::from_secs(8),
];
const OBJECT_KEY_ESCAPED_CHARACTERS: &AsciiSet = &NON_ALPHANUMERIC
    .remove(b'-')
    .remove(b'.')
    .remove(b'_')
    .remove(b'~');

pub struct IngestionConnection {
    pub base_url: String,
    pub producer_secret: String,
    pub producer_label: String,
}

pub struct IngestionClient {
    connection: IngestionConnection,
    agent: ureq::Agent,
}

struct IngestRequest<'a> {
    method: &'a str,
    endpoint: &'a str,
    content_type: &'a str,
    body: &'a [u8],
    subject: &'a str,
}

impl IngestionClient {
    pub fn new(connection: IngestionConnection) -> Result<Self> {
        if !is_permitted_ingestion_endpoint(&connection.base_url) {
            bail!(UNPERMITTED_ENDPOINT_MESSAGE);
        }
        let agent = ureq::AgentBuilder::new()
            .redirects(0)
            .timeout(INGEST_REQUEST_TIMEOUT)
            .user_agent(PUBLISHER_USER_AGENT)
            .build();
        Ok(Self { connection, agent })
    }

    pub fn publish_event(
        &self,
        topic: &str,
        schema_version: u64,
        payload: Value,
        produced_at: &str,
    ) -> Result<Map<String, Value>> {
        let event = json!({
            "topic": topic,
            "schemaVersion": schema_version,
            "producedAt": produced_at,
            "producer": self.connection.producer_label,
            "payload": payload,
        });
        let body = serde_json::to_vec(&event)?;
        self.send(&IngestRequest {
            method: "POST",
            endpoint: &self.endpoint(topic),
            content_type: "application/json",
            body: &body,
            subject: &format!("{topic} event"),
        })
        .map_err(|failure| anyhow!(failure.into_message()))
    }

    pub fn put_artifact(
        &self,
        object_key: &str,
        content_type: &str,
        body: &[u8],
    ) -> Result<Map<String, Value>> {
        let endpoint = self.endpoint(&format!(
            "artifacts/{}",
            utf8_percent_encode(object_key, OBJECT_KEY_ESCAPED_CHARACTERS)
        ));
        let request = IngestRequest {
            method: "PUT",
            endpoint: &endpoint,
            content_type,
            body,
            subject: &format!("artifact {object_key}"),
        };
        let acknowledgement = self.put_with_retries(&request)?;
        verify_artifact_echo(&acknowledgement, object_key, &request)?;
        Ok(acknowledgement)
    }

    fn put_with_retries(&self, request: &IngestRequest<'_>) -> Result<Map<String, Value>> {
        let mut last_failure = String::new();
        for delay in ARTIFACT_PUT_ATTEMPT_DELAYS {
            std::thread::sleep(delay);
            match self.send(request) {
                Ok(acknowledgement) => return Ok(acknowledgement),
                Err(IngestFailure::Transport(message)) => {
                    eprintln!("{message}");
                    last_failure = message;
                }
                Err(refused) => bail!(refused.into_message()),
            }
        }
        Err(anyhow!(last_failure))
    }

    fn endpoint(&self, path: &str) -> String {
        format!("{}/{path}", self.connection.base_url.trim_end_matches('/'))
    }

    fn send(&self, request: &IngestRequest<'_>) -> Result<Map<String, Value>, IngestFailure> {
        if !is_permitted_ingestion_endpoint(request.endpoint) {
            return Err(IngestFailure::Refused(UNPERMITTED_ENDPOINT_MESSAGE.into()));
        }
        let response = self
            .agent
            .request(request.method, request.endpoint)
            .set("content-type", request.content_type)
            .set(
                PRODUCER_AUTHENTICATION_HEADER_NAME,
                &self.connection.producer_secret,
            )
            .send_bytes(request.body);
        let (status_code, response_body) = exchange(response, request.subject)?;
        accepted_acknowledgement(status_code, &response_body, request.subject)
    }
}

fn verify_artifact_echo(
    acknowledgement: &Map<String, Value>,
    object_key: &str,
    request: &IngestRequest<'_>,
) -> Result<()> {
    let echoed = (
        acknowledgement.get("objectKey"),
        acknowledgement.get("byteLength"),
    );
    if echoed != (Some(&json!(object_key)), Some(&json!(request.body.len()))) {
        bail!(
            "the ingest api did not echo the {} objectKey and byteLength",
            request.subject
        );
    }
    Ok(())
}
