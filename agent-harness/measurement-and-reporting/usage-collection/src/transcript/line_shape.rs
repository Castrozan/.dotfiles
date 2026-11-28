use serde::Deserialize;

#[derive(Deserialize)]
pub struct TranscriptLine {
    pub timestamp: Option<String>,
    pub message: Option<AssistantMessage>,
    #[serde(rename = "costUSD")]
    pub cost_usd: Option<f64>,
    #[serde(rename = "requestId")]
    pub request_id: Option<String>,
    #[serde(rename = "isSidechain")]
    pub is_sidechain: Option<bool>,
    pub data: Option<AgentProgressData>,
}

#[derive(Deserialize)]
pub struct AgentProgressData {
    pub message: Option<AgentProgressMessage>,
}

#[derive(Deserialize)]
pub struct AgentProgressMessage {
    pub timestamp: Option<String>,
    pub message: Option<AssistantMessage>,
    #[serde(rename = "costUSD")]
    pub cost_usd: Option<f64>,
    #[serde(rename = "requestId")]
    pub request_id: Option<String>,
    #[serde(rename = "isSidechain")]
    pub is_sidechain: Option<bool>,
}

#[derive(Deserialize)]
pub struct AssistantMessage {
    pub id: Option<String>,
    pub model: Option<String>,
    pub usage: Option<MessageUsage>,
}

#[derive(Deserialize)]
pub struct MessageUsage {
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_creation_input_tokens: Option<u64>,
    pub cache_read_input_tokens: Option<u64>,
    pub cache_creation: Option<CacheCreationBreakdown>,
    pub speed: Option<String>,
}

#[derive(Deserialize)]
pub struct CacheCreationBreakdown {
    pub ephemeral_5m_input_tokens: Option<u64>,
    pub ephemeral_1h_input_tokens: Option<u64>,
}

pub struct UsageRecord {
    pub timestamp: String,
    pub message: AssistantMessage,
    pub usage: MessageUsage,
    pub cost_usd: Option<f64>,
    pub request_id: Option<String>,
    pub is_sidechain: Option<bool>,
}

impl TranscriptLine {
    pub fn into_usage_record(self) -> Option<UsageRecord> {
        if let (Some(timestamp), Some(mut message)) = (self.timestamp, self.message)
            && let Some(usage) = message.usage.take()
        {
            return Some(UsageRecord {
                timestamp,
                message,
                usage,
                cost_usd: self.cost_usd,
                request_id: self.request_id,
                is_sidechain: self.is_sidechain,
            });
        }
        let progress = self.data?.message?;
        let mut message = progress.message?;
        let usage = message.usage.take()?;
        Some(UsageRecord {
            timestamp: progress.timestamp?,
            message,
            usage,
            cost_usd: progress.cost_usd,
            request_id: progress.request_id,
            is_sidechain: progress.is_sidechain,
        })
    }
}
