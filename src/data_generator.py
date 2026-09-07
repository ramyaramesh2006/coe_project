"""
data_generator.py
Synthetic dataset and warehouse layout generator for automotive parts warehouse.
Ensures reproducible data with non-uniform aisle popularity and realistic grid paths.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional


# Standard Warehouse Layout Definition (3 rows x 4 columns = 12 Aisles)
# Coordinates in grid units (e.g., each grid unit = 15 meters)
DEFAULT_AISLES = {
    "A01": {"grid": (0, 0), "zone": "Zone_A_FastMoving", "capacity": 4, "base_prob": 0.06},
    "A02": {"grid": (0, 1), "zone": "Zone_A_FastMoving", "capacity": 4, "base_prob": 0.08},
    "A03": {"grid": (0, 2), "zone": "Zone_A_FastMoving", "capacity": 3, "base_prob": 0.22},  # High popularity hotspot
    "A04": {"grid": (0, 3), "zone": "Zone_A_FastMoving", "capacity": 5, "base_prob": 0.05},
    "A05": {"grid": (1, 0), "zone": "Zone_B_EngineParts", "capacity": 4, "base_prob": 0.06},
    "A06": {"grid": (1, 1), "zone": "Zone_B_EngineParts", "capacity": 4, "base_prob": 0.07},
    "A07": {"grid": (1, 2), "zone": "Zone_B_EngineParts", "capacity": 3, "base_prob": 0.20},  # High popularity hotspot
    "A08": {"grid": (1, 3), "zone": "Zone_B_EngineParts", "capacity": 5, "base_prob": 0.06},
    "A09": {"grid": (2, 0), "zone": "Zone_C_Electrical",  "capacity": 4, "base_prob": 0.05},
    "A10": {"grid": (2, 1), "zone": "Zone_C_Electrical",  "capacity": 4, "base_prob": 0.05},
    "A11": {"grid": (2, 2), "zone": "Zone_C_Electrical",  "capacity": 4, "base_prob": 0.05},
    "A12": {"grid": (2, 3), "zone": "Zone_C_Electrical",  "capacity": 5, "base_prob": 0.05},
}

GRID_UNIT_METERS = 15.0  # Spacing between adjacent aisle entrances


def calculate_grid_distance(
    aisle1: str,
    aisle2: str,
    aisles_def: Optional[Dict] = None,
    distance_metric: str = "manhattan"
) -> float:
    """
    Calculates distance in meters between two aisles based on layout coordinates.
    Manhattan distance is the industry standard for orthogonal warehouse grid travel.
    """
    if aisles_def is None:
        aisles_def = DEFAULT_AISLES

    if aisle1 not in aisles_def or aisle2 not in aisles_def:
        return 0.0

    x1, y1 = aisles_def[aisle1]["grid"]
    x2, y2 = aisles_def[aisle2]["grid"]

    if distance_metric == "euclidean":
        dist_units = np.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
    else:
        dist_units = abs(x1 - x2) + abs(y1 - y2)

    return float(dist_units * GRID_UNIT_METERS)


def calculate_path_total_distance(
    path: List[str],
    aisles_def: Optional[Dict] = None,
    distance_metric: str = "manhattan"
) -> float:
    """
    Calculates the total travel distance in meters for a sequence of aisles.
    Assumes travel starts at depot/staging (closest to A01 at (0,0)) and traverses the path.
    """
    if not path:
        return 0.0

    total_dist = 0.0
    # Travel from depot to first aisle
    depot_coord = (0, 0)
    first_coord = (DEFAULT_AISLES if aisles_def is None else aisles_def)[path[0]]["grid"]
    total_dist += (abs(depot_coord[0] - first_coord[0]) + abs(depot_coord[1] - first_coord[1])) * GRID_UNIT_METERS

    # Travel between consecutive aisles
    for i in range(len(path) - 1):
        total_dist += calculate_grid_distance(path[i], path[i + 1], aisles_def, distance_metric)

    return float(total_dist)


def generate_warehouse_dataset(
    num_workers: int = 120,
    num_orders: int = 350,
    seed: int = 42,
    scenario_name: str = "Normal Operation",
    peak_multiplier: float = 1.0
) -> pd.DataFrame:
    """
    Generates a realistic synthetic warehouse dataset of order pick requests and worker assignments.
    
    Parameters:
    - num_workers: Number of workers (>= 100)
    - num_orders: Number of customer pick orders (>= 300)
    - seed: Random seed for exact reproducibility
    - scenario_name: Scenario label (Normal, Peak Congestion, Sensor Failure)
    - peak_multiplier: Factor to heighten concentration on popular aisles (A03, A07)
    
    Returns:
    - pd.DataFrame containing order paths, worker assignments, entry/exit times, and distances.
    """
    np.random.seed(seed)

    aisle_names = list(DEFAULT_AISLES.keys())
    base_probs = np.array([DEFAULT_AISLES[a]["base_prob"] for a in aisle_names])

    # Adjust probabilities for peak congestion if specified
    if peak_multiplier > 1.0:
        # Heavily boost A03 and A07 (indices 2 and 6)
        probs = base_probs.copy()
        probs[2] *= peak_multiplier
        probs[6] *= peak_multiplier
        probs = probs / probs.sum()
    else:
        probs = base_probs / base_probs.sum()

    records = []
    
    # Generate orders over a 2-hour window (7200 seconds)
    simulation_duration = 7200  # seconds
    base_times = np.sort(np.random.uniform(0, simulation_duration * 0.85, size=num_orders))

    worker_pool = [f"W{i:03d}" for i in range(1, num_workers + 1)]

    for order_idx in range(num_orders):
        order_id = f"ORD_{order_idx + 1:04d}"
        worker_id = worker_pool[order_idx % num_workers]

        # Path length: 2 to 4 aisles per order
        path_length = np.random.choice([2, 3, 4], p=[0.4, 0.4, 0.2])
        chosen_aisles = list(np.random.choice(aisle_names, size=path_length, replace=False, p=probs))

        total_distance = calculate_path_total_distance(chosen_aisles)
        release_time = float(round(base_times[order_idx], 1))

        # Time spent traveling (assuming average walking speed of 1.0 m/s)
        walking_time = total_distance / 1.0
        # Time spent picking items in each aisle (between 30 and 60 seconds per aisle)
        pick_time_per_aisle = [float(round(np.random.uniform(30, 60), 1)) for _ in chosen_aisles]
        total_pick_time = sum(pick_time_per_aisle)

        current_time = release_time
        for step, aisle in enumerate(chosen_aisles):
            aisle_info = DEFAULT_AISLES[aisle]
            entry_time = float(round(current_time, 1))
            p_time = pick_time_per_aisle[step]
            exit_time = float(round(entry_time + p_time, 1))

            records.append({
                "worker_id": worker_id,
                "order_id": order_id,
                "aisle_id": aisle,
                "zone": aisle_info["zone"],
                "aisle_capacity": aisle_info["capacity"],
                "worker_entry_time": entry_time,
                "worker_exit_time": exit_time,
                "pick_time": p_time,
                "path": " -> ".join(chosen_aisles),
                "path_step": step + 1,
                "total_steps": len(chosen_aisles),
                "distance_m": total_distance,
                "release_time": release_time,
                "scenario": scenario_name,
            })
            # Advance time for next aisle (travel + pick)
            if step < len(chosen_aisles) - 1:
                leg_dist = calculate_grid_distance(aisle, chosen_aisles[step + 1])
                current_time = exit_time + (leg_dist / 1.0)
            else:
                current_time = exit_time

    df = pd.DataFrame(records)
    return df
