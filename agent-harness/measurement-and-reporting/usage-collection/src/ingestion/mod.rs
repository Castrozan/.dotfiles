mod client;
mod endpoint_policy;
mod response;

pub use client::{IngestionClient, IngestionConnection};
pub use endpoint_policy::is_permitted_ingestion_endpoint;
