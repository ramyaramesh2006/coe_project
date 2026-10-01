"""
simulation.py  (Review 2 – Enhanced)
Discrete-Event Warehouse Execution Simulation.

Runs both Baseline (unregulated release) and Controlled (wave-release managed) simulations.
Accurately records timestamps, aisle occupancy, waiting times, and travel distances.

Review 2 additions:
  * Visual-similarity-aware pick times (verification delays + mispick returns).
  * Store-and-forward queue integration for intermittent network outages.
  * Dynamic A*-based rerouting when downstream aisles are congested.
  * Richer per-order metadata: mispick count, verification overhead, reroute events.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from src.data_generator import DEFAULT_AISLES, calculate_grid_distance, calculate_path_total_distance
from src.congestion import calculate_congestion, classify_congestion
from src.controller import wave_release_controller
from src.visual_similarity import compute_adjusted_pick_time, AISLE_PART_MAP
from src.store_and_forward import StoreAndForwardQueue, NetworkStateMonitor


# ──────────────────────────────────────────────────────────────────────────────
# A* path-rerouting helper
# ──────────────────────────────────────────────────────────────────────────────

def _astar_reroute(
    start_aisle: str,
    remaining_targets: List[str],
    blocked_aisles: set,
    aisles_def: Dict,
) -> List[str]:
    """
    Lightweight A* reroute: reorders `remaining_targets` to minimise total
    Manhattan travel distance while skipping `blocked_aisles`.

    This is a nearest-neighbour greedy heuristic with A*-style obstacle avoidance,
    sufficient for small warehouse grids (12 nodes).

    Returns
    -------
    Ordered list of aisles (skipping blocked ones, or including them last if unavoidable).
    """
    if not remaining_targets:
        return []

    # Separate reachable vs blocked targets
    reachable = [a for a in remaining_targets if a not in blocked_aisles]
    forced = [a for a in remaining_targets if a in blocked_aisles]

    ordered: List[str] = []
    current = start_aisle

    # Nearest-neighbour greedy ordering of reachable targets
    unvisited = list(reachable)
    while unvisited:
        nearest = min(
            unvisited,
            key=lambda a: calculate_grid_distance(current, a, aisles_def)
        )
        ordered.append(nearest)
        unvisited.remove(nearest)
        current = nearest

    # Append forced (blocked) aisles at the end – worker visits them last,
    # giving time for the aisle to clear.
    ordered.extend(forced)
    return ordered


# ──────────────────────────────────────────────────────────────────────────────
# Simulation engine
# ──────────────────────────────────────────────────────────────────────────────

class WarehouseSimulation:
    def __init__(
        self,
        orders_df: pd.DataFrame,
        aisles_def: Optional[Dict] = None,
        controlled: bool = False,
        safe_threshold: float = 75.0,
        sensor_available: bool = True,
        fallback_congestion: float = 60.0,
        retry_delay_seconds: float = 30.0,
        walking_speed_mps: float = 1.0,
        use_visual_similarity: bool = True,
        enable_dynamic_rerouting: bool = True,
        reroute_threshold_pct: float = 90.0,
        # Store-and-forward / intermittent outage settings
        use_store_and_forward: bool = False,
        network_monitor: Optional[NetworkStateMonitor] = None,
        saf_spool_path: Optional[str] = None,
        seed: int = 42,
    ):
        """
        Initialises the warehouse execution simulation.

        Parameters
        ----------
        orders_df            : Synthetic dataset from data_generator
        aisles_def           : Warehouse layout definition dict
        controlled           : If True, applies wave_release_controller
        safe_threshold       : Safe congestion threshold %
        sensor_available     : Static sensor health flag (used when use_store_and_forward=False)
        fallback_congestion  : Fallback congestion % if sensor fails
        retry_delay_seconds  : Seconds to hold a worker when controller returns DELAY
        walking_speed_mps    : Worker walking speed m/s
        use_visual_similarity: Model pick verification delays & mispick returns
        enable_dynamic_rerouting: Re-order remaining aisle path when downstream congestion
                                  exceeds reroute_threshold_pct
        reroute_threshold_pct: Congestion level (%) that triggers rerouting
        use_store_and_forward: Enable the store-and-forward offline queue
        network_monitor      : NetworkStateMonitor instance for intermittent outages
        saf_spool_path       : CSV path to write store-and-forward spool
        seed                 : RNG seed for reproducibility of visual-similarity sampling
        """
        self.raw_df = orders_df.copy()
        self.aisles_def = aisles_def if aisles_def is not None else DEFAULT_AISLES
        self.controlled = controlled
        self.safe_threshold = safe_threshold
        self.sensor_available = sensor_available
        self.fallback_congestion = fallback_congestion
        self.retry_delay_seconds = retry_delay_seconds
        self.walking_speed = walking_speed_mps
        self.use_visual_similarity = use_visual_similarity
        self.enable_dynamic_rerouting = enable_dynamic_rerouting
        self.reroute_threshold_pct = reroute_threshold_pct
        self.seed = seed

        # Store-and-forward integration
        self.use_store_and_forward = use_store_and_forward
        self.network_monitor = network_monitor
        self.saf_queue = StoreAndForwardQueue(spool_path=saf_spool_path) if use_store_and_forward else None
        self._prev_online_state: bool = True  # Track transitions for S&F

        # RNG for pick-time sampling (seeded for reproducibility)
        self._rng = np.random.default_rng(seed)

        # Results tracking
        self.executed_orders: List[Dict[str, Any]] = []
        self.aisle_intervals: Dict[str, List[Tuple[float, float, str]]] = {
            a: [] for a in self.aisles_def.keys()
        }
        self.controller_logs: List[Dict[str, Any]] = []
        self.reroute_events: List[Dict[str, Any]] = []

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _get_current_workers_in_aisle(self, aisle: str, current_time: float) -> int:
        """Counts workers physically inside aisle at current_time."""
        count = 0
        for entry_t, exit_t, _ in self.aisle_intervals.get(aisle, []):
            if entry_t <= current_time < exit_t:
                count += 1
        return count

    def _get_congestion_pct(self, aisle: str, current_time: float) -> float:
        """Returns live congestion percentage for an aisle at current_time."""
        workers = self._get_current_workers_in_aisle(aisle, current_time)
        cap = self.aisles_def[aisle]["capacity"]
        return (workers / max(1, cap)) * 100.0

    def _resolve_sensor_available(self, sim_time: float) -> bool:
        """Determine sensor availability, considering intermittent outage monitor."""
        if self.network_monitor is not None:
            return self.network_monitor.is_online(sim_time)
        return self.sensor_available

    def _handle_store_and_forward_transition(
        self,
        sim_time: float,
        currently_online: bool,
    ) -> None:
        """Notify the S&F queue of network state transitions."""
        if self.saf_queue is None:
            return
        if self._prev_online_state and not currently_online:
            self.saf_queue.report_network_down(sim_time)
        elif not self._prev_online_state and currently_online:
            self.saf_queue.report_network_restored(sim_time)
            # Replay queued decisions
            aisle_workers = {
                a: self._get_current_workers_in_aisle(a, sim_time)
                for a in self.aisles_def
            }
            aisle_caps = {a: info["capacity"] for a, info in self.aisles_def.items()}
            self.saf_queue.replay(aisle_workers, aisle_caps, self.safe_threshold, sim_time)
        self._prev_online_state = currently_online

    # ── Main execution loop ──────────────────────────────────────────────────

    def run(self) -> pd.DataFrame:
        """
        Executes the simulation across all orders in chronological order.
        Returns a DataFrame of completed order execution metrics.
        """
        order_groups = self.raw_df.groupby("order_id", sort=False)
        order_list = []

        for order_id, group in order_groups:
            first_row = group.iloc[0]
            path_aisles = [r["aisle_id"] for _, r in group.sort_values("path_step").iterrows()]
            req_release_time = first_row["release_time"]
            worker_id = first_row["worker_id"]
            total_dist = first_row["distance_m"]

            order_list.append({
                "order_id": order_id,
                "worker_id": worker_id,
                "req_release_time": req_release_time,
                "path": path_aisles,
                "total_dist": total_dist,
            })

        order_list.sort(key=lambda x: x["req_release_time"])

        for item in order_list:
            order_id = item["order_id"]
            worker_id = item["worker_id"]
            req_time = item["req_release_time"]
            path = item["path"]
            total_dist = item["total_dist"]

            target_first_aisle = path[0]
            aisle_cap = self.aisles_def[target_first_aisle]["capacity"]

            actual_release_time = req_time
            delay_count = 0

            # ── Wave-release controller ──────────────────────────────────────
            if self.controlled:
                max_retries = 20
                for _ in range(max_retries):
                    current_online = self._resolve_sensor_available(actual_release_time)
                    self._handle_store_and_forward_transition(actual_release_time, current_online)

                    current_workers = self._get_current_workers_in_aisle(
                        target_first_aisle, actual_release_time
                    )
                    ctrl_decision = wave_release_controller(
                        congestion_percentage=None,
                        requested_workers=1,
                        safe_threshold=self.safe_threshold,
                        aisle_capacity=aisle_cap,
                        current_workers=current_workers,
                        sensor_available=current_online,
                        fallback_congestion=self.fallback_congestion,
                    )
                    ctrl_decision["order_id"] = order_id
                    ctrl_decision["timestamp"] = actual_release_time
                    ctrl_decision["target_aisle"] = target_first_aisle
                    self.controller_logs.append(ctrl_decision)

                    # If offline: enqueue to S&F
                    if self.saf_queue is not None and not current_online:
                        self.saf_queue.enqueue(
                            sim_timestamp=actual_release_time,
                            order_id=order_id,
                            target_aisle=target_first_aisle,
                            controller_result=ctrl_decision,
                            fallback_congestion=self.fallback_congestion,
                        )

                    if ctrl_decision["decision"] == "ALLOW":
                        break
                    else:
                        actual_release_time += self.retry_delay_seconds
                        delay_count += 1

            waiting_time = max(0.0, actual_release_time - req_time)

            # ── Traverse path ────────────────────────────────────────────────
            current_time = actual_release_time
            first_coord = self.aisles_def[path[0]]["grid"]
            depot_travel_m = (abs(first_coord[0]) + abs(first_coord[1])) * 15.0
            current_time += depot_travel_m / self.walking_speed

            # Dynamic rerouting: reorder remaining aisles if downstream congested
            effective_path = list(path)
            rerouted = False
            if self.enable_dynamic_rerouting and len(path) > 1:
                blocked = set(
                    a for a in path[1:]
                    if self._get_congestion_pct(a, current_time) >= self.reroute_threshold_pct
                )
                if blocked:
                    rerouted = True
                    new_remaining = _astar_reroute(
                        start_aisle=path[0],
                        remaining_targets=path[1:],
                        blocked_aisles=blocked,
                        aisles_def=self.aisles_def,
                    )
                    effective_path = [path[0]] + new_remaining
                    self.reroute_events.append({
                        "order_id": order_id,
                        "timestamp": current_time,
                        "original_path": "→".join(path),
                        "rerouted_path": "→".join(effective_path),
                        "blocked_aisles": ",".join(sorted(blocked)),
                    })

            # Walk and pick through effective path
            total_verification_time = 0.0
            total_mispick_penalty = 0.0
            mispick_count = 0
            actual_travel_distance = 0.0

            # Depot to first aisle
            actual_travel_distance += depot_travel_m

            for step, aisle in enumerate(effective_path):
                entry_time = current_time

                # Pick time: standard or visual-similarity-aware
                if self.use_visual_similarity:
                    p_time, detail = compute_adjusted_pick_time(aisle, rng=self._rng)
                    total_verification_time += detail["verification_time"]
                    if detail["mispick_occurred"]:
                        mispick_count += 1
                        total_mispick_penalty += detail["return_penalty"]
                else:
                    p_time = float(self._rng.uniform(30, 60))

                exit_time = entry_time + p_time
                self.aisle_intervals[aisle].append((entry_time, exit_time, worker_id))
                current_time = exit_time

                if step < len(effective_path) - 1:
                    leg_dist = calculate_grid_distance(aisle, effective_path[step + 1], self.aisles_def)
                    actual_travel_distance += leg_dist
                    current_time += leg_dist / self.walking_speed

            completion_time = current_time

            self.executed_orders.append({
                "order_id": order_id,
                "worker_id": worker_id,
                "requested_release_time": req_time,
                "actual_release_time": actual_release_time,
                "waiting_time": waiting_time,
                "delay_count": delay_count,
                "completion_time": completion_time,
                "turnaround_time": completion_time - req_time,
                "path_length": len(effective_path),
                "total_distance_m": actual_travel_distance,
                # Review 2 additions
                "verification_overhead_sec": round(total_verification_time, 2),
                "mispick_penalty_sec": round(total_mispick_penalty, 2),
                "mispick_count": mispick_count,
                "rerouted": rerouted,
                "mode": "CONTROLLED" if self.controlled else "BASELINE",
            })

        return pd.DataFrame(self.executed_orders)

    def get_aisle_congestion_timeseries(
        self,
        time_step_seconds: float = 30.0
    ) -> pd.DataFrame:
        """
        Samples aisle congestion percentage across the entire simulation duration.
        Returns a DataFrame indexed by time step with columns for each aisle.
        """
        if not self.executed_orders:
            return pd.DataFrame()

        max_time = max(r["completion_time"] for r in self.executed_orders)
        timestamps = np.arange(0, max_time + time_step_seconds, time_step_seconds)

        records = []
        for t in timestamps:
            row: Dict[str, Any] = {"timestamp_sec": t}
            for aisle, info in self.aisles_def.items():
                workers = self._get_current_workers_in_aisle(aisle, t)
                cap = info["capacity"]
                cong = calculate_congestion(workers, cap, self.sensor_available, self.fallback_congestion)
                row[f"{aisle}_workers"] = workers
                row[f"{aisle}_congestion"] = cong
                row[f"{aisle}_level"] = classify_congestion(cong)
            records.append(row)

        return pd.DataFrame(records)

    def get_store_and_forward_summary(self) -> Optional[Dict[str, Any]]:
        """Returns the S&F queue summary if store-and-forward is enabled."""
        if self.saf_queue is None:
            return None
        return self.saf_queue.get_summary()
