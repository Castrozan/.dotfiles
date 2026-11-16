import sys
import time
import urllib.parse


from ingestion_snapshot_publisher import (
    IngestionRefusedError,
    IngestionTransportError,
    create_authenticated_ingestion_request,
    read_ingest_connection,
    send_ingest_request,
)

ARTIFACT_PUT_ATTEMPT_DELAYS_SECONDS = (0, 2, 8)


def build_artifact_endpoint_url(ingest_base_url, object_key):
    encoded_object_key = urllib.parse.quote(object_key, safe="")
    return f"{ingest_base_url.rstrip('/')}/artifacts/{encoded_object_key}"


def send_idempotent_artifact_put(request, subject):
    for attempt_delay_seconds in ARTIFACT_PUT_ATTEMPT_DELAYS_SECONDS[:-1]:
        time.sleep(attempt_delay_seconds)
        try:
            return send_ingest_request(request, subject)
        except IngestionTransportError as transport_failure:
            print(transport_failure, file=sys.stderr)
    time.sleep(ARTIFACT_PUT_ATTEMPT_DELAYS_SECONDS[-1])
    return send_ingest_request(request, subject)


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
    acknowledgement = send_idempotent_artifact_put(request, subject)
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
