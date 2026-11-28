use serde_json::{Map, Value};

const ACCEPTED_INGEST_STATUS_CODE: u16 = 202;

pub enum IngestFailure {
    Transport(String),
    Refused(String),
}

impl IngestFailure {
    pub fn into_message(self) -> String {
        match self {
            Self::Transport(message) | Self::Refused(message) => message,
        }
    }
}

pub fn exchange(
    response: Result<ureq::Response, ureq::Error>,
    subject: &str,
) -> Result<(u16, String), IngestFailure> {
    let (status_code, response) = match response {
        Ok(response) => (response.status(), response),
        Err(ureq::Error::Status(status_code, response)) => (status_code, response),
        Err(ureq::Error::Transport(transport)) => return Err(unfinished(subject, transport)),
    };
    let response_body = response
        .into_string()
        .map_err(|failure| unfinished(subject, failure))?;
    Ok((status_code, response_body))
}

pub fn accepted_acknowledgement(
    status_code: u16,
    response_body: &str,
    subject: &str,
) -> Result<Map<String, Value>, IngestFailure> {
    if status_code != ACCEPTED_INGEST_STATUS_CODE {
        return Err(IngestFailure::Refused(format!(
            "the ingest api refused the {subject} with status {status_code}: {}",
            refusal_message(response_body)
        )));
    }
    match serde_json::from_str::<Value>(response_body) {
        Ok(Value::Object(acknowledgement)) => Ok(acknowledgement),
        _ => Err(IngestFailure::Refused(format!(
            "the ingest api acknowledged the {subject} with no JSON object"
        ))),
    }
}

fn refusal_message(response_body: &str) -> String {
    let reported_error = serde_json::from_str::<Value>(response_body)
        .ok()
        .and_then(|document| document.get("error").cloned());
    match reported_error {
        Some(Value::String(text)) => text,
        Some(other) => other.to_string(),
        None => response_body.to_string(),
    }
}

fn unfinished(subject: &str, failure: impl std::fmt::Display) -> IngestFailure {
    IngestFailure::Transport(format!(
        "the ingest request could not finish for the {subject}: {failure}"
    ))
}
