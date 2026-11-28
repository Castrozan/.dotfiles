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

impl AssistantMessage {
    fn split_usage(mut self) -> Option<(Self, MessageUsage)> {
        let usage = self.usage.take()?;
        Some((self, usage))
    }
}

impl TranscriptLine {
    pub fn into_usage_record(self) -> Option<UsageRecord> {
        let direct_message = self.message.and_then(AssistantMessage::split_usage);
        match (self.timestamp, direct_message) {
            (Some(timestamp), Some((message, usage))) => Some(UsageRecord {
                timestamp,
                message,
                usage,
                cost_usd: self.cost_usd,
                request_id: self.request_id,
                is_sidechain: self.is_sidechain,
            }),
            _ => self.data?.message?.into_usage_record(),
        }
    }
}

impl AgentProgressMessage {
    fn into_usage_record(self) -> Option<UsageRecord> {
        let (message, usage) = self.message?.split_usage()?;
        Some(UsageRecord {
            timestamp: self.timestamp?,
            message,
            usage,
            cost_usd: self.cost_usd,
            request_id: self.request_id,
            is_sidechain: self.is_sidechain,
        })
    }
}
