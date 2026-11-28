mod client;
mod endpoint_policy;

pub use client::{IngestionClient, IngestionConnection};
pub use endpoint_policy::is_permitted_ingestion_endpoint;
