use claude_usage_collector::ingestion::{
    IngestionClient, IngestionConnection, is_permitted_ingestion_endpoint,
};

#[test]
fn permits_https_and_explicit_loopback_http() {
    for endpoint in [
        "https://lucaszanoni.com/ingest",
        "https://lucaszanoni.com:8443/ingest/",
        "http://localhost:8787/ingest",
        "http://127.0.0.1/ingest",
        "http://[::1]:8787/ingest",
    ] {
        assert!(is_permitted_ingestion_endpoint(endpoint), "{endpoint}");
    }
}

#[test]
fn refuses_endpoints_that_could_leak_the_producer_secret() {
    for endpoint in [
        "http://lucaszanoni.com/ingest",
        "http://127.0.0.2/ingest",
        "https://user:pass@lucaszanoni.com/ingest",
        "https://user@lucaszanoni.com/ingest",
        "https://lucaszanoni.com/ingest?redirect=x",
        "https://lucaszanoni.com/ingest#fragment",
        "https://lucaszanoni.com:0/ingest",
        "https://lucaszanoni.com/in gest",
        "https://lucaszanoni.com\\@evil.example/ingest",
        "ftp://lucaszanoni.com/ingest",
        "lucaszanoni.com/ingest",
        "",
    ] {
        assert!(!is_permitted_ingestion_endpoint(endpoint), "{endpoint}");
    }
}

#[test]
fn will_not_build_a_client_for_a_refused_base_url() {
    let connection = IngestionConnection {
        base_url: "http://lucaszanoni.com/ingest".into(),
        producer_secret: "secret".into(),
        producer_label: "dotfiles-usage-exporter".into(),
    };
    assert!(IngestionClient::new(connection).is_err());
}
