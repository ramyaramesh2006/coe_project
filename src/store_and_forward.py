"""
store_and_forward.py
Offline Store-and-Forward Queue for Sensor / Network Failure Mode.

Review 1 feedback:
    "Evolve the current manual fallback into an offline store-and-forward queue mechanism
     when edge telemetry drops."

This module provides:
- StoreAndForwardQueue : persists dispatch decisions while the network is down.
- ReplayEngine         : replays queued events when connectivity is restored.
- NetworkStateMonitor  : simulates intermittent outages and reconnections.
- Integration hooks    : used by simulation.py to switch between ONLINE / OFFLINE modes.

Design decisions
----------------
*  When the sensor/network is unavailable the controller does NOT crash.  Instead
   every ALLOW/DELAY/BLOCK decision is stamped and appended to an in-memory
   store-and-forward queue (simulating an edge-device local SQLite / CSV spool).
*  On reconnection the replay engine drains the queue in FIFO order and reconciles
   each stored decision against the current real-time aisle state.
*  All queued events are also written to `results/store_forward_log.csv` so
   stakeholders can audit what happened during the outage.
"""

from __future__ import annotations

import csv
import os
import time
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Deque, Dict, Any, List, Optional


# ──────────────────────────────────────────────────────────────────────────────
# 1. Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class QueuedEvent:
    """A single controller dispatch decision stored while offline."""
    event_id: int
    sim_timestamp: float          # Simulation time (seconds)
    wall_clock: float             # Real wall-clock epoch at enqueue
    order_id: str
    target_aisle: str
    decision: str                 # ALLOW | DELAY | BLOCK
    effective_congestion: float
    fallback_congestion: float
    reason: str
    mode: str                     # MANUAL FALLBACK | AUTOMATIC
    system_status: str            # SENSOR FAILURE | NORMAL
    replayed: bool = False
    replay_timestamp: Optional[float] = None
    reconciliation_outcome: str = "PENDING"


@dataclass
class OutageWindow:
    """Records a single network outage episode."""
    outage_id: int
    start_time: float
    end_time: Optional[float] = None
    events_queued: int = 0
    events_replayed: int = 0

    @property
    def duration_sec(self) -> Optional[float]:
        if self.end_time is not None:
            return round(self.end_time - self.start_time, 2)
        return None


# ──────────────────────────────────────────────────────────────────────────────
# 2. Store-and-Forward Queue
# ──────────────────────────────────────────────────────────────────────────────

class StoreAndForwardQueue:
    """
    Persists controller dispatch events during a network/sensor outage.

    Thread-safety note: this implementation is single-threaded (simulation context).
    For a real embedded edge device, wrap methods with asyncio.Lock / threading.Lock.
    """

    def __init__(self, spool_path: Optional[str] = None):
        """
        Parameters
        ----------
        spool_path : Optional path to write a CSV spool file (audit trail).
                     If None, the queue is in-memory only.
        """
        self._queue: Deque[QueuedEvent] = deque()
        self._event_counter: int = 0
        self._outage_history: List[OutageWindow] = []
        self._current_outage: Optional[OutageWindow] = None
        self._network_online: bool = True
        self._spool_path: Optional[str] = spool_path

        if spool_path:
            os.makedirs(os.path.dirname(spool_path), exist_ok=True)

    # ── Network state management ────────────────────────────────────────────

    def report_network_down(self, sim_time: float) -> None:
        """Call this when the sensor/network connection drops."""
        if self._network_online:
            self._network_online = False
            outage_id = len(self._outage_history) + 1
            self._current_outage = OutageWindow(
                outage_id=outage_id,
                start_time=sim_time
            )

    def report_network_restored(self, sim_time: float) -> None:
        """Call this when connectivity is re-established."""
        if not self._network_online and self._current_outage is not None:
            self._current_outage.end_time = sim_time
            self._outage_history.append(self._current_outage)
            self._current_outage = None
        self._network_online = True

    @property
    def is_online(self) -> bool:
        return self._network_online

    @property
    def queue_depth(self) -> int:
        return len(self._queue)

    # ── Event enqueue ───────────────────────────────────────────────────────

    def enqueue(
        self,
        sim_timestamp: float,
        order_id: str,
        target_aisle: str,
        controller_result: Dict[str, Any],
        fallback_congestion: float,
    ) -> QueuedEvent:
        """
        Stores a controller decision in the spool while the network is down.

        Parameters
        ----------
        sim_timestamp     : Current simulation time in seconds
        order_id          : The order being dispatched
        target_aisle      : First aisle on the order path
        controller_result : Dict returned by wave_release_controller()
        fallback_congestion : Conservative estimate used during offline mode
        """
        self._event_counter += 1
        event = QueuedEvent(
            event_id=self._event_counter,
            sim_timestamp=sim_timestamp,
            wall_clock=time.time(),
            order_id=order_id,
            target_aisle=target_aisle,
            decision=controller_result.get("decision", "DELAY"),
            effective_congestion=controller_result.get("effective_congestion", fallback_congestion),
            fallback_congestion=fallback_congestion,
            reason=controller_result.get("reason", "Offline store-and-forward"),
            mode=controller_result.get("mode", "MANUAL FALLBACK"),
            system_status=controller_result.get("system_status", "SENSOR FAILURE"),
        )
        self._queue.append(event)

        if self._current_outage is not None:
            self._current_outage.events_queued += 1

        if self._spool_path:
            self._write_to_spool(event)

        return event

    def _write_to_spool(self, event: QueuedEvent) -> None:
        """Appends one event row to the CSV spool file (simulates edge-device flush)."""
        file_exists = os.path.isfile(self._spool_path)
        with open(self._spool_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(asdict(event).keys()))
            if not file_exists:
                writer.writeheader()
            writer.writerow(asdict(event))

    # ── Drain / replay ──────────────────────────────────────────────────────

    def drain(self) -> List[QueuedEvent]:
        """
        Returns all queued events in FIFO order without removing them.
        Call replay() to mark them as replayed.
        """
        return list(self._queue)

    def replay(
        self,
        current_aisle_workers: Dict[str, int],
        aisle_capacities: Dict[str, int],
        safe_threshold: float,
        sim_time: float,
    ) -> List[Dict[str, Any]]:
        """
        Replays queued events against current real-time aisle state on reconnection.

        For each queued event:
          - Re-evaluates whether the ALLOW / DELAY / BLOCK decision is still valid.
          - Records the reconciliation outcome (CONFIRMED | OVERRIDDEN).
          - Marks the event as replayed.
          - Updates the CSV spool if configured.

        Returns a list of reconciliation records for logging/reporting.
        """
        reconciliation_log = []
        replayed_count = 0

        while self._queue:
            event = self._queue.popleft()

            # Re-evaluate congestion with real data
            workers_now = current_aisle_workers.get(event.target_aisle, 0)
            capacity_now = aisle_capacities.get(event.target_aisle, 4)
            live_congestion = (workers_now / max(1, capacity_now)) * 100.0

            # Determine if original decision still holds
            if live_congestion < safe_threshold:
                new_decision = "ALLOW"
            elif live_congestion < 100.0:
                new_decision = "DELAY"
            else:
                new_decision = "BLOCK"

            reconciliation_outcome = (
                "CONFIRMED" if new_decision == event.decision else "OVERRIDDEN"
            )

            event.replayed = True
            event.replay_timestamp = sim_time
            event.reconciliation_outcome = reconciliation_outcome

            replayed_count += 1

            reconciliation_log.append({
                "event_id": event.event_id,
                "order_id": event.order_id,
                "target_aisle": event.target_aisle,
                "original_decision": event.decision,
                "live_congestion_at_replay": round(live_congestion, 2),
                "new_decision": new_decision,
                "reconciliation_outcome": reconciliation_outcome,
                "replay_timestamp": sim_time,
            })

        # Update last outage's replayed count
        if self._outage_history:
            self._outage_history[-1].events_replayed = replayed_count

        return reconciliation_log

    # ── Reporting ───────────────────────────────────────────────────────────

    def get_summary(self) -> Dict[str, Any]:
        """Returns a diagnostic summary of store-and-forward activity."""
        total_queued = sum(w.events_queued for w in self._outage_history)
        total_replayed = sum(w.events_replayed for w in self._outage_history)
        total_outages = len(self._outage_history)
        total_outage_duration = sum(
            w.duration_sec or 0.0 for w in self._outage_history
        )

        return {
            "total_outages": total_outages,
            "total_outage_duration_sec": round(total_outage_duration, 2),
            "total_events_queued": total_queued,
            "total_events_replayed": total_replayed,
            "current_queue_depth": self.queue_depth,
            "network_currently_online": self.is_online,
            "outage_windows": [
                {
                    "outage_id": w.outage_id,
                    "start_time": w.start_time,
                    "end_time": w.end_time,
                    "duration_sec": w.duration_sec,
                    "events_queued": w.events_queued,
                    "events_replayed": w.events_replayed,
                }
                for w in self._outage_history
            ],
        }


# ──────────────────────────────────────────────────────────────────────────────
# 3. Network State Monitor (simulates intermittent outages)
# ──────────────────────────────────────────────────────────────────────────────

class NetworkStateMonitor:
    """
    Simulates realistic intermittent IoT sensor/network outages.

    Usage
    -----
    monitor = NetworkStateMonitor(
        total_sim_duration=7200,
        mean_outage_interval=900,   # Outage every ~15 min on average
        mean_outage_duration=180,   # Each lasts ~3 min on average
        seed=42
    )
    # At each simulation tick:
    is_online = monitor.is_online(sim_time)
    """

    def __init__(
        self,
        total_sim_duration: float = 7200.0,
        mean_outage_interval: float = 900.0,
        mean_outage_duration: float = 180.0,
        seed: int = 42,
    ):
        import numpy as _np

        # Generate outage start times as a Poisson process
        rng = _np.random.default_rng(seed)

        inter_arrival = rng.exponential(mean_outage_interval, size=20)
        start_times = _np.cumsum(inter_arrival)
        durations = rng.exponential(mean_outage_duration, size=20)

        self._outage_intervals: List[tuple] = []
        for s, d in zip(start_times, durations):
            if s < total_sim_duration:
                self._outage_intervals.append((float(s), float(s + d)))

    def is_online(self, sim_time: float) -> bool:
        """Returns True if the network is available at `sim_time`."""
        for start, end in self._outage_intervals:
            if start <= sim_time < end:
                return False
        return True

    def get_outage_schedule(self) -> List[Dict[str, float]]:
        """Returns the full list of simulated outage windows."""
        return [
            {"start_sec": s, "end_sec": e, "duration_sec": round(e - s, 2)}
            for s, e in self._outage_intervals
        ]
