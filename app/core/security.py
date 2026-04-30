import hashlib
import hmac


def verify_github_signature(
    payload: bytes,
    signature_header: str | None,
    secret: str,
) -> bool:
    """
    Verify the GitHub webhook signature.

    GitHub sends the signature in the format:
    sha256=<hex_digest>
    """
    if not signature_header:
        return False

    if not signature_header.startswith("sha256="):
        return False

    received_signature = signature_header.split("=", 1)[1]

    expected_signature = hmac.new(
        key=secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(received_signature, expected_signature)
