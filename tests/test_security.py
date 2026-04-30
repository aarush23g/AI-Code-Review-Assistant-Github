import hashlib
import hmac

from app.core.security import verify_github_signature


def test_verify_github_signature_valid() -> None:
    payload = b'{"hello":"world"}'
    secret = "test-secret"

    digest = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    signature = f"sha256={digest}"

    assert verify_github_signature(payload, signature, secret) is True


def test_verify_github_signature_invalid() -> None:
    payload = b'{"hello":"world"}'
    secret = "test-secret"
    bad_signature = "sha256=invalid"

    assert verify_github_signature(payload, bad_signature, secret) is False
