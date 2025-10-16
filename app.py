import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

st.set_page_config(page_title="Device Analytics Dashboard", layout="wide")
st.title("Device Analytics Dashboard")

# ----------------------
# Load datasets
# ----------------------
mode_data = pd.read_csv("EL_with_mode.csv", parse_dates=["created_at", "updated_at"])
onoff_data = pd.read_csv("EL_with_mode_onoff.csv", parse_dates=["created_at", "updated_at"])
fail_data = pd.read_csv("EL_with_mode_onoff_failure.csv", parse_dates=["created_at", "updated_at"])
rest_data = pd.read_csv("EL_resting_summary_minutes.csv")
monthly_data = pd.read_csv("monthly_device_usage.csv")

# ----------------------
# Load water analytics CSV
# ----------------------
water_data = pd.read_csv("chart_water_analytics.csv")
water_data.rename(columns={
    water_data.columns[1]: "uid",
    water_data.columns[2]: "height_of_water",
    water_data.columns[3]: "water_level_below_surface",
    water_data.columns[5]: "timestamp"
}, inplace=True)
water_data["timestamp"] = pd.to_datetime(water_data["timestamp"])

rest_data.rename(columns={"uiuid": "uid"}, inplace=True)

# ----------------------
# Sidebar Filters
# ----------------------
uids = mode_data["uid"].unique()
selected_uid = st.sidebar.selectbox("Select Device UID", uids)

months = monthly_data["month"].unique()
selected_months = st.sidebar.multiselect("Select Month(s)", months, default=months)

# ----------------------
# Filter data based on selections
# ----------------------
mode_filtered = mode_data[mode_data["uid"] == selected_uid]
onoff_filtered = onoff_data[onoff_data["uid"] == selected_uid]
fail_filtered = fail_data[(fail_data["uid"] == selected_uid) &
                          (fail_data["created_at"].dt.to_period("M").astype(str).isin(selected_months))]
rest_filtered = rest_data[(rest_data["uid"] == selected_uid)]
monthly_filtered = monthly_data[(monthly_data["uid"] == selected_uid) &
                                (monthly_data["month"].isin(selected_months))]
water_filtered = water_data[water_data["uid"] == selected_uid]

# ----------------------
# Top KPIs
# ----------------------
total_runtime = monthly_filtered["runtime_hours"].sum()
total_water = monthly_filtered["water_yield_liters"].sum()
total_power = monthly_filtered["power_consumed_KVA"].sum()
total_failures = len(fail_filtered)

st.markdown("### Device Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Runtime (hrs)", round(total_runtime, 2))
col2.metric("Total Water Yield (L)", round(total_water, 2))
col3.metric("Total Power Consumed (kVA)", round(total_power, 2))
col4.metric("Failure Count", total_failures)

st.markdown("---")

# ----------------------
# 1️⃣ Device Mode Distribution
# ----------------------
st.subheader("1️⃣ Device Mode Distribution")
mode_counts = mode_filtered["mode"].value_counts().reset_index()
mode_counts.columns = ["mode", "count"]
fig_mode = px.pie(mode_counts, names="mode", values="count",
                  color="mode", color_discrete_map={"REMOTE":"blue","MANUAL":"orange"},
                  hole=0.4, title=f"Mode Distribution for Device {selected_uid}")
st.plotly_chart(fig_mode, use_container_width=True)
st.caption(
    "📊 Pie chart shows how much time the device operated in REMOTE (blue) vs MANUAL (orange). "
    "Each slice represents the proportion of time spent in that mode. Helps understand mode preferences."
)

# ============================
# 2. Runtime vs Water Level (Bagalkunte) — Interactive with Hover & White Background
# ============================

st.subheader("2️⃣ Relationship Between Pump Runtime and Water Level (Bagalkunte)")

import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

# --- Define base path ---
base_path = os.path.dirname(__file__)

# --- Load CSV files ---
water_level_path = os.path.join(base_path, "water level bk final.csv")
runtime_path = os.path.join(base_path, "runtime bagalkunte.csv")

# Read data
wl_df = pd.read_csv(water_level_path)
runtime_df = pd.read_csv(runtime_path)

# Merge with runtime
merged_data = pd.merge(runtime_df, wl_df, on='category')

# Clean column names
merged_data.rename(columns={
    'category': 'Date',
    'Height of Water': 'Water_Level_Below_Surface',
    'Total Runtime (hrs)': 'Runtime_hrs'
}, inplace=True)

# Handle missing values
merged_data['Runtime_hrs'].fillna(merged_data['Runtime_hrs'].mean(), inplace=True)
merged_data['Water_Level_Below_Surface'].fillna(merged_data['Water_Level_Below_Surface'].mean(), inplace=True)

# Remove zero runtime points for better trend line calculation
merged_data = merged_data[merged_data['Runtime_hrs'] > 0]

# Only for Bagalkunte UID
merged_data['UID'] = '865357062795388'

# --- Create interactive scatter plot with Plotly ---
fig = px.scatter(
    merged_data,
    x='Runtime_hrs',
    y='Water_Level_Below_Surface',
    color='Date',
    hover_data={
        'Runtime_hrs': True,
        'Water_Level_Below_Surface': True,
        'Date': True
    },
    labels={
        'Runtime_hrs': 'Total Runtime (hours)',
        'Water_Level_Below_Surface': 'Water Level Below Surface (m)'
    },
    title='Bagalkunte UID: 865357062795388 — Pump Runtime vs Water Level'
)

# --- Add trend line (linear regression) ---
z = np.polyfit(merged_data['Runtime_hrs'], merged_data['Water_Level_Below_Surface'], 1)
p = np.poly1d(z)
fig.add_trace(
    go.Scatter(
        x=merged_data['Runtime_hrs'],
        y=p(merged_data['Runtime_hrs']),
        mode='lines',
        name='Trend Line',
        line=dict(color='red', dash='dash'),
        hoverinfo='y+x+name'
    )
)

# --- Invert y-axis to match original Matplotlib version ---
fig.update_yaxes(autorange="reversed")

# --- Set white background and grid similar to Matplotlib ---
fig.update_layout(
    xaxis=dict(showgrid=True, gridcolor='lightgray'),
    yaxis=dict(showgrid=True, gridcolor='lightgray'),
    legend=dict(title='Date', bordercolor='lightgray', borderwidth=1)
)

# --- Render in Streamlit ---
st.plotly_chart(fig, use_container_width=True)

# --- Caption ---
st.caption(
    "💧 This scatter plot shows the **drawdown effect at Bagalkunte (UID: 865357062795388)**. "
    "Hover over points or the trend line to see the exact runtime and water level. "
    "The red dashed trend line now correctly shows that **longer pump runtimes lead to lower water levels**, "
    "demonstrating how pumping decreases water below surface."
)

# ----------------------
# 3️⃣ Failure Analytics
# ----------------------
st.subheader("3️⃣ Failure Analytics")
if not fail_filtered.empty:
    fail_counts = fail_filtered.groupby("failure_type").size().reset_index(name="count")
    if fail_counts.empty:
        st.warning(f"No failure data available for Device {selected_uid} in the selected period.")
    else:
        fig_fail = px.treemap(
            fail_counts,
            path=["failure_type"],
            values="count",
            color="count",
            color_continuous_scale="Reds",
            title=f"Failure Type Distribution for Device {selected_uid}"
        )
        st.plotly_chart(fig_fail, use_container_width=True)
        top_failure = fail_counts.iloc[fail_counts['count'].idxmax()]
        st.caption(
            f"🛑 Treemap shows frequency of different failure types for Device {selected_uid}. "
            f"The most common failure was **{top_failure['failure_type']}**, occurring **{top_failure['count']} times**. "
            "Helps identify failure patterns and maintenance priorities."
        )
else:
    st.info("No failures recorded for this device.")

# ----------------------
# 4️⃣ Resting Time Between OFF → Next ON (Violin Plot)
# ----------------------
st.subheader("4️⃣ Resting Time Between Cycles")
if not onoff_filtered.empty:
    onoff_filtered = onoff_filtered.sort_values("created_at")
    rest_list = []
    previous_off_time = None
    for idx, row in onoff_filtered.iterrows():
        if row["on_off_status"] == "OFF":
            previous_off_time = row["created_at"]
        elif row["on_off_status"] == "ON" and previous_off_time is not None:
            delta = (row["created_at"] - previous_off_time).total_seconds()/60
            rest_list.append({"timestamp": row["created_at"], "resting_minutes": delta})
            previous_off_time = None
    rest_df = pd.DataFrame(rest_list)
    if not rest_df.empty:
        rest_df["month"] = rest_df["timestamp"].dt.to_period("M").astype(str)
        fig_rest = px.violin(rest_df, x="month", y="resting_minutes", box=True, points="all",
                             color_discrete_sequence=["skyblue"],
                             title=f"Resting Time Distribution for Device {selected_uid}")
        fig_rest.update_layout(xaxis_title="Month", yaxis_title="Resting Time (minutes)")
        st.plotly_chart(fig_rest, use_container_width=True)
        st.caption(
            "⏱ Violin plot shows resting time between OFF → next ON for the device per month. "
            "Longer violins or higher median = more rest between cycles. Helps understand downtime patterns."
        )
    else:
        st.info("Not enough OFF → ON transitions to compute resting time.")
else:
    st.info("No On/Off data for this device.")

# ----------------------
# 5️⃣ Efficiency Metrics per Month (Bubble Chart)
# ----------------------
st.subheader("5️⃣ Efficiency Metrics per Month")
if not monthly_filtered.empty:
    monthly_filtered_sorted = monthly_filtered.sort_values("month")
    monthly_filtered_sorted["month_name"] = pd.to_datetime(
        monthly_filtered_sorted["month"].astype(str), format="%Y-%m").dt.strftime("%b %Y")
    
    fig_bubble = px.scatter(monthly_filtered_sorted, x="runtime_hours", y="power_consumed_KVA",
                            size="water_yield_liters", color="month_name",
                            hover_data={"month_name":True, "runtime_hours":True,
                                        "power_consumed_KVA":True, "water_yield_liters":True},
                            title=f"Device {selected_uid} Efficiency Bubble Chart")
    fig_bubble.update_layout(xaxis_title="Runtime (hrs)", yaxis_title="Power Consumed (kVA)")
    st.plotly_chart(fig_bubble, use_container_width=True)
    st.caption(
        "💡 Bubble chart shows efficiency per month. X-axis = Runtime hours, Y-axis = Power consumed, "
        "Bubble size = Water Yield (L). Helps identify which months had high water yield with lower runtime and power."
    )
else:
    st.info("No monthly usage data available for this device.")

st.markdown("---")
st.markdown("📌 Use the sidebar to select different UID or month for analysis.")