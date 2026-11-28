use std::net::{Ipv4Addr, Ipv6Addr};

use url::{Host, Url};

const LOOPBACK_HOSTNAME: &str = "localhost";

fn is_forbidden_endpoint_character(character: char) -> bool {
    character == '\\' || (character as u32) <= 32 || (character as u32) == 127
}

pub fn is_permitted_ingestion_endpoint(value: &str) -> bool {
    if value.chars().any(is_forbidden_endpoint_character) {
        return false;
    }
    let Ok(endpoint) = Url::parse(value) else {
        return false;
    };
    has_valid_authority(&endpoint)
        && has_no_credentials_or_suffix(&endpoint)
        && has_permitted_transport(&endpoint)
}

fn has_valid_authority(endpoint: &Url) -> bool {
    endpoint.host().is_some() && endpoint.port() != Some(0)
}

fn has_no_credentials_or_suffix(endpoint: &Url) -> bool {
    endpoint.username().is_empty()
        && endpoint.password().is_none()
        && endpoint.query().is_none()
        && endpoint.fragment().is_none()
}

fn has_permitted_transport(endpoint: &Url) -> bool {
    match endpoint.scheme() {
        "https" => true,
        "http" => is_loopback_host(endpoint),
        _ => false,
    }
}

fn is_loopback_host(endpoint: &Url) -> bool {
    match endpoint.host() {
        Some(Host::Domain(name)) => name == LOOPBACK_HOSTNAME,
        Some(Host::Ipv4(address)) => address == Ipv4Addr::LOCALHOST,
        Some(Host::Ipv6(address)) => address == Ipv6Addr::LOCALHOST,
        None => false,
    }
}
