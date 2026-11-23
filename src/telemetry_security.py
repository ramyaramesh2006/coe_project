"""Review 3 telemetry integrity protection using HMAC-SHA256.

This is a simulation-layer control, not a replacement for TLS, device identity,
secure key provisioning, or hardware-backed key storage.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional, Set, Tuple


def _canonical_message(payload: Dict[str, Any], timestamp: float, nonce: str) -> bytes:
    """Serialize signed fields deterministically so sender and receiver agree."""
    body = {"payload": payload, "timestamp": float(timestamp), "nonce": str(nonce)}
    return json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sign_telemetry(payload: Dict[str, Any], secret_key: bytes, timestamp: float, nonce: str) -> str:
    """Return an HMAC-SHA256 hex digest for a telemetry payload."""
    if not secret_key:
        raise ValueError("secret_key must not be empty")
    if not isinstance(payload, dict):
        raise TypeError("payload must be a dictionary")
    if not nonce:
        raise ValueError("nonce must not be empty")
    return hmac.new(secret_key, _canonical_message(payload, timestamp, nonce), hashlib.sha256).hexdigest()


def verify_telemetry_signature(
    payload: Dict[str, Any], signature: str, secret_key: bytes, timestamp: float, nonce: str
) -> bool:
    """Verify a telemetry signature using a constant-time digest comparison."""
    if not secret_key or not signature or not nonce:
        return False
    expected = sign_telemetry(payload, secret_key, timestamp, nonce)
    return hmac.compare_digest(expected, str(signature))


class TelemetryAuthenticator:
    """Verify signature, freshness and nonce uniqueness for simulated sensor packets."""

    def __init__(self, secret_key: bytes, max_age_seconds: float = 30.0,
                 future_tolerance_seconds: float = 5.0):
        if not secret_key:
            raise ValueError("secret_key must not be empty")
        if max_age_seconds < 0 or future_tolerance_seconds < 0:
            raise ValueError("time tolerances must be non-negative")
        self._secret_key = secret_key
        self.max_age_seconds = float(max_age_seconds)
        self.future_tolerance_seconds = float(future_tolerance_seconds)
        self._seen_nonces: Set[str] = set()

    def create_packet(self, payload: Dict[str, Any], timestamp: Optional[float] = None,
                      nonce: str = "") -> Dict[str, Any]:
        """Create a signed packet; production devices must use cryptographically random nonces."""
        packet_time = time.time() if timestamp is None else float(timestamp)
        if not nonce:
            raise ValueError("nonce must be supplied by the caller")
        signature = sign_telemetry(payload, self._secret_key, packet_time, nonce)
        return {"payload": payload, "timestamp": packet_time, "nonce": nonce, "signature": signature}

    def verify_packet(self, packet: Dict[str, Any], now: Optional[float] = None) -> Tuple[bool, str]:
        """Return (accepted, reason); rejected packets never consume a nonce."""
        if not isinstance(packet, dict):
            return False, "INVALID_PACKET"
        required = {"payload", "timestamp", "nonce", "signature"}
        if not required.issubset(packet):
            return False, "MISSING_FIELDS"
        try:
            packet_time = float(packet["timestamp"])
            nonce = str(packet["nonce"])
            payload = packet["payload"]
            signature = str(packet["signature"])
            current_time = time.time() if now is None else float(now)
        except (TypeError, ValueError):
            return False, "INVALID_FIELDS"
        if not nonce:
            return False, "INVALID_NONCE"
        if nonce in self._seen_nonces:
            return False, "REPLAY_DETECTED"
        age = current_time - packet_time
        if age > self.max_age_seconds:
            return False, "STALE_PACKET"
        if age < -self.future_tolerance_seconds:
            return False, "FUTURE_TIMESTAMP"
        try:
            valid = verify_telemetry_signature(payload, signature, self._secret_key, packet_time, nonce)
        except (TypeError, ValueError):
            return False, "INVALID_SIGNATURE"
        if not valid:
            return False, "INVALID_SIGNATURE"
        self._seen_nonces.add(nonce)
        return True, "ACCEPTED"
