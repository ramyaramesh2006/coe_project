import pandas as pd

from src.simulation import WarehouseSimulation


def test_controlled_entry_uses_projected_occupancy_for_each_aisle():
    # Three simultaneous orders target A03 (capacity 3). The first two may enter
    # while projected occupancy remains below 75%; the third must wait until
    # an earlier pick interval clears.
    data = pd.DataFrame([
        {
            "order_id": f"ORD_{index:04d}",
            "worker_id": f"W{index:03d}",
            "aisle_id": "A03",
            "path_step": 1,
            "release_time": 0.0,
            "distance_m": 30.0,
        }
        for index in range(1, 4)
    ])
    simulation = WarehouseSimulation(
        data,
        controlled=True,
        safe_threshold=75.0,
        use_visual_similarity=False,
        enable_dynamic_rerouting=False,
        walking_speed_mps=1.0,
    )
    result = simulation.run()
    time_series = simulation.get_aisle_congestion_timeseries(time_step_seconds=1.0)

    assert len(result) == 3
    allowed = [
        log for log in simulation.controller_logs
        if log["target_aisle"] == "A03" and log["decision"] == "ALLOW"
    ]
    assert allowed
    assert all(log["effective_congestion"] < 75.0 for log in allowed)
    assert any(log["decision"] in {"DELAY", "BLOCK"} for log in simulation.controller_logs)
    assert float(time_series["A03_congestion"].max()) < 75.0
