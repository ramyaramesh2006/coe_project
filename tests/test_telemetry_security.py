import pytest

from src.telemetry_security import (
    TelemetryAuthenticator,
    sign_telemetry,
    verify_telemetry_signature,
)


KEY = b"unit-test-only-secret"


def test_valid_hmac_signature_is_accepted():
    payload = {"aisle_id": "A03", "workers": 2, "capacity": 3}
    signature = sign_telemetry(payload, KEY, 100.0, "nonce-1")
    assert verify_telemetry_signature(payload, signature, KEY, 100.0, "nonce-1")


def test_tampered_payload_is_rejected():
    payload = {"aisle_id": "A03", "workers": 2}
    signature = sign_telemetry(payload, KEY, 100.0, "nonce-2")
    assert not verify_telemetry_signature({**payload, "workers": 0}, signature, KEY, 100.0, "nonce-2")


def test_wrong_key_is_rejected():
    signature = sign_telemetry({"workers": 1}, KEY, 100.0, "nonce-3")
    assert not verify_telemetry_signature({"workers": 1}, signature, b"wrong-key", 100.0, "nonce-3")


def test_empty_key_is_rejected():
    with pytest.raises(ValueError):
        sign_telemetry({"workers": 1}, b"", 100.0, "nonce-4")


def test_stale_packet_is_rejected():
    auth = TelemetryAuthenticator(KEY, max_age_seconds=10)
    packet = auth.create_packet({"workers": 1}, timestamp=100, nonce="stale")
    assert auth.verify_packet(packet, now=111) == (False, "STALE_PACKET")


def test_replay_is_rejected_after_first_acceptance():
    auth = TelemetryAuthenticator(KEY)
    packet = auth.create_packet({"workers": 1}, timestamp=100, nonce="repeat")
    assert auth.verify_packet(packet, now=101) == (True, "ACCEPTED")
    assert auth.verify_packet(packet, now=101) == (False, "REPLAY_DETECTED")


def test_future_packet_outside_tolerance_is_rejected():
    auth = TelemetryAuthenticator(KEY, future_tolerance_seconds=2)
    packet = auth.create_packet({"workers": 1}, timestamp=110, nonce="future")
    assert auth.verify_packet(packet, now=100) == (False, "FUTURE_TIMESTAMP")


def test_invalid_signature_does_not_consume_nonce():
    auth = TelemetryAuthenticator(KEY)
    packet = auth.create_packet({"workers": 1}, timestamp=100, nonce="retry")
    packet["signature"] = "0" * 64
    assert auth.verify_packet(packet, now=101) == (False, "INVALID_SIGNATURE")
    packet = auth.create_packet({"workers": 1}, timestamp=100, nonce="retry")
    assert auth.verify_packet(packet, now=101) == (True, "ACCEPTED")
