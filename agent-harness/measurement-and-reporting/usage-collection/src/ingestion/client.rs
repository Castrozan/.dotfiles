use std::time::Duration;

use anyhow::{Result, anyhow, bail};
use percent_encoding::{AsciiSet, NON_ALPHANUMERIC, utf8_percent_encode};
use serde_json::{Map, Value, json};

use super::endpoint_policy::is_permitted_ingestion_endpoint;

const PRODUCER_AUTHENTICATION_HEADER_NAME: &str = "x-ingest-producer-secret";
const PUBLISHER_USER_AGENT: &str = "dotfiles-ingestion-publisher/1";
const ACCEPTED_INGEST_STATUS_CODE: u16 = 202;
const INGEST_REQUEST_TIMEOUT: Duration = Duration::from_secs(30);
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

enum IngestFailure {
    Transport(String),
    Refused(String),
}

pub struct IngestionClient {
    connection: IngestionConnection,
    agent: ureq::Agent,
}

impl IngestionClient {
    pub fn new(connection: IngestionConnection) -> Result<Self> {
        if !is_permitted_ingestion_endpoint(&connection.base_url) {
            bail!(
                "Ingestion requires credential-free HTTPS or explicit loopback HTTP without query or fragment"
            );
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
        let subject = format!("{topic} event");
        self.send(
            "POST",
            &self.endpoint(topic),
            "application/json",
            &body,
            &subject,
        )
        .map_err(|failure| anyhow!(failure_message(failure)))
    }

    pub fn put_artifact(
        &self,
        object_key: &str,
        content_type: &str,
        body: &[u8],
    ) -> Result<Map<String, Value>> {
        let subject = format!("artifact {object_key}");
        let endpoint = self.endpoint(&format!(
            "artifacts/{}",
            utf8_percent_encode(object_key, OBJECT_KEY_ESCAPED_CHARACTERS)
        ));
        let mut last_failure = None;
        for delay in ARTIFACT_PUT_ATTEMPT_DELAYS {
            std::thread::sleep(delay);
            match self.send("PUT", &endpoint, content_type, body, &subject) {
                Ok(acknowledgement) => {
                    let echoed = (
                        acknowledgement.get("objectKey"),
                        acknowledgement.get("byteLength"),
                    );
                    if echoed != (Some(&json!(object_key)), Some(&json!(body.len()))) {
                        bail!("the ingest api did not echo the {subject} objectKey and byteLength");
                    }
                    return Ok(acknowledgement);
                }
                Err(IngestFailure::Transport(message)) => {
                    eprintln!("{message}");
                    last_failure = Some(message);
                }
                Err(refused) => bail!(failure_message(refused)),
            }
        }
        Err(anyhow!(last_failure.unwrap_or_default()))
    }

    fn endpoint(&self, path: &str) -> String {
        format!("{}/{path}", self.connection.base_url.trim_end_matches('/'))
    }

    fn send(
        &self,
        method: &str,
        endpoint: &str,
        content_type: &str,
        body: &[u8],
        subject: &str,
    ) -> Result<Map<String, Value>, IngestFailure> {
        if !is_permitted_ingestion_endpoint(endpoint) {
            return Err(IngestFailure::Refused(
                "Ingestion requires credential-free HTTPS or explicit loopback HTTP without query or fragment".into(),
            ));
        }
        let response = self
            .agent
            .request(method, endpoint)
            .set("content-type", content_type)
            .set(
                PRODUCER_AUTHENTICATION_HEADER_NAME,
                &self.connection.producer_secret,
            )
            .send_bytes(body);
        let (status_code, response_body) = match response {
            Ok(response) => (response.status(), response.into_string()),
            Err(ureq::Error::Status(status_code, response)) => {
                (status_code, response.into_string())
            }
            Err(ureq::Error::Transport(transport)) => {
                return Err(IngestFailure::Transport(format!(
                    "the ingest request could not finish for the {subject}: {transport}"
                )));
            }
        };
        let response_body = response_body.map_err(|failure| {
            IngestFailure::Transport(format!(
                "the ingest request could not finish for the {subject}: {failure}"
            ))
        })?;
        if status_code != ACCEPTED_INGEST_STATUS_CODE {
            let reported_error = serde_json::from_str::<Value>(&response_body)
                .ok()
                .and_then(|document| document.get("error").cloned())
                .map_or(response_body.clone(), |error| match error {
                    Value::String(text) => text,
                    other => other.to_string(),
                });
            return Err(IngestFailure::Refused(format!(
                "the ingest api refused the {subject} with status {status_code}: {reported_error}"
            )));
        }
        match serde_json::from_str::<Value>(&response_body) {
            Ok(Value::Object(acknowledgement)) => Ok(acknowledgement),
            _ => Err(IngestFailure::Refused(format!(
                "the ingest api acknowledged the {subject} with no JSON object"
            ))),
        }
    }
}

fn failure_message(failure: IngestFailure) -> String {
    match failure {
        IngestFailure::Transport(message) | IngestFailure::Refused(message) => message,
    }
}
