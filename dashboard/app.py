"""Interactive Review 3 floor dashboard.

Run from the repository root:
    pip install -r requirements-dashboard.txt
    streamlit run dashboard/app.py
"""
from pathlib import Path
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_generator import DEFAULT_AISLES, generate_warehouse_dataset
from src.simulation import WarehouseSimulation

st.set_page_config(page_title="Warehouse Review 3 Dashboard", layout="wide")
st.title("Aisle Congestion Simulator — Review 3 Floor Dashboard")
st.caption("Synthetic simulation view: worker travel, pick activity and aisle capacity.")

with st.sidebar:
    st.header("Simulation controls")
    scenario = st.selectbox("Operating scenario", ["Normal", "Peak", "Extreme"])
    order_count = st.slider("Orders to simulate", 20, 150, 60, 10)
    controlled = st.toggle("Enable wave-release controller", value=True)
    seed = st.number_input("Random seed", min_value=0, max_value=999999, value=42)

peak = {"Normal": 1.0, "Peak": 2.8, "Extreme": 3.5}[scenario]
workers = {"Normal": 40, "Peak": 60, "Extreme": 80}[scenario]
data = generate_warehouse_dataset(
    num_workers=workers, num_orders=order_count, seed=int(seed),
    scenario_name=scenario, peak_multiplier=peak,
)
sim = WarehouseSimulation(data, controlled=controlled, seed=int(seed))
orders = sim.run()
trace = sim.get_movement_trace()
timeline = sim.get_aisle_congestion_timeseries(time_step_seconds=30)

if orders.empty or trace.empty:
    st.warning("No simulation records were generated for these settings.")
    st.stop()

duration = float(trace["end_time"].max())
time_value = st.slider("Simulation time (seconds)", 0.0, max(duration, 1.0), 0.0, 5.0)
active = trace[(trace["start_time"] <= time_value) & (trace["end_time"] >= time_value)].copy()

layout = go.Figure()
for aisle_id, info in DEFAULT_AISLES.items():
    x, y = info["grid"]
    cap = info["capacity"]
    congestion_col = f"{aisle_id}_congestion"
    row = timeline.iloc[(timeline["timestamp_sec"] - time_value).abs().argsort()[:1]]
    congestion = float(row.iloc[0][congestion_col]) if not row.empty else 0.0
    layout.add_trace(go.Scatter(
        x=[x], y=[-y], mode="markers+text",
        marker={"size": 28, "color": congestion, "colorscale": "RdYlGn_r",
                "cmin": 0, "cmax": 120, "showscale": True,
                "line": {"width": 1, "color": "#333"}},
        text=[f"{aisle_id}<br>{congestion:.0f}% / cap {cap}"],
        textposition="bottom center", name=aisle_id,
        hovertemplate=f"{aisle_id}<br>Congestion: {congestion:.1f}%<br>Capacity: {cap}<extra></extra>",
    ))
if not active.empty:
    for _, seg in active.iterrows():
        span = max(float(seg["end_time"] - seg["start_time"]), 0.001)
        fraction = min(1.0, max(0.0, (time_value - float(seg["start_time"])) / span))
        px = float(seg["start_x"]) + fraction * (float(seg["end_x"]) - float(seg["start_x"]))
        py = float(seg["start_y"]) + fraction * (float(seg["end_y"]) - float(seg["start_y"]))
        layout.add_trace(go.Scatter(
            x=[px], y=[-py], mode="markers",
            marker={"size": 12, "symbol": "circle", "color": "#145da0"},
            name=f"{seg['worker_id']} / {seg['order_id']}",
            hovertemplate=f"Worker {seg['worker_id']}<br>Order {seg['order_id']}<br>{seg['event']}<extra></extra>",
            showlegend=False,
        ))
layout.update_layout(
    title=f"{scenario} warehouse floor — t={time_value:.0f}s",
    xaxis_title="Warehouse grid X", yaxis_title="Warehouse grid Y",
    yaxis={"scaleanchor": "x", "scaleratio": 1},
    height=650, legend={"orientation": "h"},
)
st.plotly_chart(layout, use_container_width=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Orders completed", len(orders))
c2.metric("Average waiting time", f"{orders['waiting_time'].mean():.1f} s")
c3.metric("Throughput", f"{len(orders) / max((orders['completion_time'].max() - orders['requested_release_time'].min()) / 3600, 1/3600):.1f} orders/hr")
c4.metric("Rerouted orders", int(orders["rerouted"].sum()))

st.subheader("Aisle occupancy at selected time")
occupancy = timeline.iloc[(timeline["timestamp_sec"] - time_value).abs().argsort()[:1]]
if not occupancy.empty:
    rows = []
    for aisle_id, info in DEFAULT_AISLES.items():
        rows.append({
            "Aisle": aisle_id, "Workers": int(occupancy.iloc[0][f"{aisle_id}_workers"]),
            "Capacity": int(info["capacity"]),
            "Congestion (%)": float(occupancy.iloc[0][f"{aisle_id}_congestion"]),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("Order execution sample")
st.dataframe(orders.head(20), use_container_width=True, hide_index=True)
