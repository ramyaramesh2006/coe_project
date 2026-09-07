"""
controller.py
Wave-Release Controller for Aisle Congestion Management.
Regulates worker flow into warehouse aisles based on congestion thresholds and sensor health.
"""

from typing import Dict, Any, Optional
from src.congestion import calculate_congestion, classify_congestion, DEFAULT_THRESHOLDS


def wave_release_controller(
    congestion_percentage: Optional[float] = None,
    requested_workers: int = 1,
    safe_threshold: float = 75.0,
    aisle_capacity: int = 4,
    current_workers: Optional[int] = None,
    sensor_available: bool = True,
    fallback_congestion: float = 60.0,
    thresholds: Optional[Dict[str, float]] = None
) -> Dict[str, Any]:
    """
    Decides whether to ALLOW, DELAY, or BLOCK worker releases into a targeted warehouse aisle.

    Parameters:
    - congestion_percentage: Measured aisle congestion (%). If None, computed from current_workers & aisle_capacity.
    - requested_workers: Number of workers requesting entry (default: 1).
    - safe_threshold: Safe congestion threshold % (default: 75.0%).
    - aisle_capacity: Maximum worker capacity of the target aisle.
    - current_workers: Number of workers currently in the aisle.
    - sensor_available: Boolean flag indicating sensor/network health.
    - fallback_congestion: Presumed congestion percentage in manual fallback mode.
    - thresholds: Dictionary of classification thresholds.

    Returns:
    - dict containing:
      {
        'decision': 'ALLOW' | 'DELAY' | 'BLOCK',
        'released_workers': int,
        'delayed_workers': int,
        'effective_congestion': float,
        'congestion_level': str,
        'reason': str,
        'system_status': 'NORMAL' | 'SENSOR FAILURE',
        'mode': 'AUTOMATIC' | 'MANUAL FALLBACK'
      }
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    # Handle Sensor / Network Failure
    if not sensor_available:
        eff_congestion = float(fallback_congestion)
        level = classify_congestion(eff_congestion, thresholds)
        # In manual fallback, use conservative fixed-rate pacing (allow at most 1 worker)
        released = min(requested_workers, 1) if eff_congestion < safe_threshold else 0
        delayed = requested_workers - released
        decision = "ALLOW" if released > 0 else "DELAY"
        reason = (
            f"Sensor telemetry offline. Fallback mode active (estimated congestion: {eff_congestion:.1f}%). "
            f"Paced release applied."
        )
        return {
            "decision": decision,
            "released_workers": released,
            "delayed_workers": delayed,
            "effective_congestion": eff_congestion,
            "congestion_level": level,
            "reason": reason,
            "system_status": "SENSOR FAILURE",
            "mode": "MANUAL FALLBACK"
        }

    # Compute congestion if not directly provided
    if congestion_percentage is None:
        workers = current_workers if current_workers is not None else 0
        eff_congestion = calculate_congestion(workers, aisle_capacity, sensor_available=True)
    else:
        eff_congestion = float(congestion_percentage)

    level = classify_congestion(eff_congestion, thresholds)

    # Controller Decision Rules
    if eff_congestion < thresholds.get("LOW_MAX", 50.0):
        # LOW congestion: completely safe to release all
        decision = "ALLOW"
        released = requested_workers
        delayed = 0
        reason = f"Congestion is LOW ({eff_congestion:.1f}% < 50%). Full release granted."

    elif eff_congestion < safe_threshold:
        # MEDIUM congestion but below safe threshold: safe to release
        decision = "ALLOW"
        released = requested_workers
        delayed = 0
        reason = f"Congestion is MEDIUM ({eff_congestion:.1f}% < safe threshold {safe_threshold:.1f}%). Release allowed."

    elif eff_congestion < 100.0:
        # HIGH congestion (between safe threshold and 100%): Delay excess workers
        # Only allow 1 worker if strictly needed, or delay all to let aisle clear
        decision = "DELAY"
        released = 0
        delayed = requested_workers
        reason = (
            f"Congestion is HIGH ({eff_congestion:.1f}% >= safe threshold {safe_threshold:.1f}%). "
            f"Holding release to mitigate bottleneck formation."
        )

    else:
        # CRITICAL congestion (>= 100%): Immediate BLOCK / Strong delay
        decision = "BLOCK"
        released = 0
        delayed = requested_workers
        reason = (
            f"Congestion is CRITICAL ({eff_congestion:.1f}% >= 100%). "
            f"Aisle saturated. Releases strictly blocked until clearance."
        )

    return {
        "decision": decision,
        "released_workers": released,
        "delayed_workers": delayed,
        "effective_congestion": eff_congestion,
        "congestion_level": level,
        "reason": reason,
        "system_status": "NORMAL",
        "mode": "AUTOMATIC"
    }
