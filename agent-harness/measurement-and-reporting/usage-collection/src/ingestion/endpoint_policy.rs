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
        "http" => {
            matches!(endpoint.host(), Some(Host::Domain(LOOPBACK_HOSTNAME)))
                || endpoint.host() == Some(Host::Ipv4(Ipv4Addr::LOCALHOST))
                || endpoint.host() == Some(Host::Ipv6(Ipv6Addr::LOCALHOST))
        }
        _ => false,
    }
}
