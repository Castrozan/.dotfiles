import urllib.parse


from ingestion_snapshot_publisher import (
    IngestionRefusedError,
    create_authenticated_ingestion_request,
    read_ingest_connection,
    send_ingest_request,
)


def build_artifact_endpoint_url(ingest_base_url, object_key):
    encoded_object_key = urllib.parse.quote(object_key, safe="")
    return f"{ingest_base_url.rstrip('/')}/artifacts/{encoded_object_key}"


def put_artifact(
    ingest_base_url, producer_secret, object_key, content_type, body_bytes
):
    subject = f"artifact {object_key}"
    request = create_authenticated_ingestion_request(
        build_artifact_endpoint_url(ingest_base_url, object_key),
        producer_secret,
        content_type,
        body_bytes,
        "PUT",
    )
    acknowledgement = send_ingest_request(request, subject)
    echoed = (acknowledgement.get("objectKey"), acknowledgement.get("byteLength"))
    if echoed != (object_key, len(body_bytes)):
        raise IngestionRefusedError(
            f"the ingest api did not echo the {subject} objectKey and byteLength"
        )
    return acknowledgement


def publish_artifact(object_key, content_type, body_bytes, environment):
    ingest_base_url, producer_secret = read_ingest_connection(environment)
    return put_artifact(
        ingest_base_url, producer_secret, object_key, content_type, body_bytes
    )
