from src.data_generator import generate_warehouse_dataset
from src.simulation import WarehouseSimulation


def test_movement_trace_contains_timestamped_travel_and_pick_segments():
    data = generate_warehouse_dataset(num_workers=4, num_orders=5, seed=17)
    simulation = WarehouseSimulation(
        data, controlled=False, use_visual_similarity=False,
        enable_dynamic_rerouting=False, seed=17,
    )
    result = simulation.run()
    trace = simulation.get_movement_trace()

    assert not result.empty
    assert not trace.empty
    assert {"worker_id", "order_id", "event", "start_time", "end_time",
            "start_x", "start_y", "end_x", "end_y"}.issubset(trace.columns)
    assert set(trace["event"]).issubset({"TRAVEL", "PICK"})
    assert (trace["end_time"] >= trace["start_time"]).all()
    assert trace[["start_x", "start_y", "end_x", "end_y"]].notna().all().all()


def test_movement_trace_pick_segments_match_aisle_identifiers():
    data = generate_warehouse_dataset(num_workers=4, num_orders=5, seed=17)
    simulation = WarehouseSimulation(data, use_visual_similarity=False,
                                     enable_dynamic_rerouting=False, seed=17)
    simulation.run()
    trace = simulation.get_movement_trace()
    picks = trace[trace["event"] == "PICK"]
    assert not picks.empty
    assert picks["aisle_id"].notna().all()
