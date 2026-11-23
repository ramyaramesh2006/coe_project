from src.data_generator import generate_warehouse_dataset
from src.simulation import WarehouseSimulation
from src.telemetry_security import TelemetryAuthenticator


def _small_dataset():
    return generate_warehouse_dataset(num_workers=8, num_orders=8, seed=73)


def test_valid_authenticated_telemetry_is_used_by_controller():
    auth = TelemetryAuthenticator(b"review3-test-key")
    sim = WarehouseSimulation(
        _small_dataset(), controlled=True, use_visual_similarity=False,
        enable_dynamic_rerouting=False, telemetry_authenticator=auth,
    )
    result = sim.run()
    summary = sim.get_telemetry_security_summary()

    assert len(result) == 8
    assert summary["packets_checked"] > 0
    assert summary["packets_accepted"] == summary["packets_checked"]
    assert summary["packets_rejected"] == 0
    assert all(log["mode"] == "AUTOMATIC" for log in sim.controller_logs)


def test_tampered_telemetry_forces_manual_fallback_and_is_rejected():
    auth = TelemetryAuthenticator(b"review3-test-key")
    sim = WarehouseSimulation(
        _small_dataset(), controlled=True, fallback_congestion=65.0,
        use_store_and_forward=True, use_visual_similarity=False,
        enable_dynamic_rerouting=False, telemetry_authenticator=auth,
        telemetry_tamper_order_ids={"ORD_0001"},
    )
    sim.run()

    assert len(sim.telemetry_rejections) == 1
    assert sim.telemetry_rejections[0]["reason"] == "INVALID_SIGNATURE"
    fallback_logs = [log for log in sim.controller_logs if log["mode"] == "MANUAL FALLBACK"]
    assert fallback_logs
    assert fallback_logs[0]["system_status"] == "SENSOR FAILURE"
    summary = sim.get_store_and_forward_summary()
    assert summary is not None
    assert summary["total_events_queued"] >= 1


def test_security_summary_counts_accepted_and_rejected_packets():
    auth = TelemetryAuthenticator(b"review3-test-key")
    sim = WarehouseSimulation(
        _small_dataset(), controlled=True, use_visual_similarity=False,
        enable_dynamic_rerouting=False, telemetry_authenticator=auth,
        telemetry_tamper_order_ids={"ORD_0001", "ORD_0002"},
    )
    sim.run()
    summary = sim.get_telemetry_security_summary()

    assert summary["packets_rejected"] == 2
    assert summary["packets_accepted"] > 0
    assert summary["packets_checked"] == summary["packets_accepted"] + summary["packets_rejected"]
