import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Device Analytics Dashboard", layout="wide")

st.title(" Device Analytics Dashboard ")

# ----------------------
# Load datasets
# ----------------------
mode_data = pd.read_csv("EL_with_mode.csv", parse_dates=["created_at", "updated_at"])
onoff_data = pd.read_csv("EL_with_mode_onoff.csv", parse_dates=["created_at", "updated_at"])
fail_data = pd.read_csv("EL_with_mode_onoff_failure.csv", parse_dates=["created_at", "updated_at"])
rest_data = pd.read_csv("EL_resting_summary_minutes.csv")
monthly_data = pd.read_csv("monthly_device_usage.csv")

# Ensure consistent column names
rest_data.rename(columns={"uiuid": "uid"}, inplace=True)

# ----------------------
# Sidebar Filters
# ----------------------
uids = mode_data["uid"].unique()
selected_uid = st.sidebar.selectbox("Select Device UID", uids)

months = monthly_data["month"].unique()
selected_months = st.sidebar.multiselect("Select Month(s)", months, default=months)

# Filter data based on selections
mode_filtered = mode_data[mode_data["uid"] == selected_uid]
onoff_filtered = onoff_data[onoff_data["uid"] == selected_uid]
fail_filtered = fail_data[fail_data["uid"] == selected_uid]
rest_filtered = rest_data[rest_data["uid"] == selected_uid]
monthly_filtered = monthly_data[(monthly_data["uid"] == selected_uid) & (monthly_data["month"].isin(selected_months))]

# ----------------------
# Top KPIs
# ----------------------
# Filtered failures for selected months
fail_filtered_by_month = fail_filtered[
    (fail_filtered["created_at"].dt.to_period("M").astype(str).isin(selected_months))
]

total_runtime = monthly_filtered["runtime_hours"].sum()
total_water = monthly_filtered["water_yield_liters"].sum()
total_power = monthly_filtered["power_consumed_KVA"].sum()
total_failures = len(fail_filtered_by_month)

st.markdown("###  Device Summary Metrics")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Runtime (hrs)", round(total_runtime, 2))
col2.metric("Total Water Yield (L)", round(total_water, 2))
col3.metric("Total Power Consumed (kVA)", round(total_power, 2))
col4.metric("Failure Count", total_failures)

st.markdown("---")

# ----------------------
# 1. Mode Distribution
# ----------------------
st.subheader("1️ Device Mode Distribution")
mode_counts = mode_filtered["mode"].value_counts().reset_index()
mode_counts.columns = ["mode", "count"]

remote_count = int(mode_counts[mode_counts["mode"]=="REMOTE"]["count"].values[0]) if "REMOTE" in mode_counts["mode"].values else 0
manual_count = int(mode_counts[mode_counts["mode"]=="MANUAL"]["count"].values[0]) if "MANUAL" in mode_counts["mode"].values else 0

fig_mode = px.pie(mode_counts, names="mode", values="count",
                  color="mode", color_discrete_map={"REMOTE":"blue","MANUAL":"orange"},
                  hole=0.4, title="Mode Distribution")
st.plotly_chart(fig_mode, use_container_width=True)
st.caption(
    f"This device operated {remote_count} times in REMOTE mode and {manual_count} times in MANUAL mode. "
    "Blue portion = REMOTE mode, Orange = MANUAL. Helps see which mode dominates for this device."
)

# ----------------------
# 2. On/Off Cycles - Enhanced with Plain-Language Caption
# ----------------------
st.subheader("2️ Start/Stop Frequency and Patterns")
if not onoff_filtered.empty:
    onoff_filtered["timestamp"] = pd.to_datetime(onoff_filtered["created_at"])
    onoff_filtered["date"] = onoff_filtered["timestamp"].dt.date

    # Aggregate frequency of ON events per day
    on_freq = onoff_filtered[onoff_filtered["on_off_status"]=="ON"].groupby("date").size().reset_index(name="count")
    
    fig_onoff = px.bar(on_freq, x="date", y="count",
                       color="count", color_continuous_scale="Viridis",
                       title="Daily Frequency of Start Events")
    fig_onoff.update_layout(xaxis_title="Date", yaxis_title="Number of Start Events")
    st.plotly_chart(fig_onoff, use_container_width=True)
    
    on_freq_total = on_freq["count"].sum()
    max_start_day = on_freq.loc[on_freq["count"].idxmax(), "date"] if not on_freq.empty else None
    
    st.caption(
        f"In the selected month(s), this device was started a total of {on_freq_total} times. "
        f"The most active day was {max_start_day} with {on_freq['count'].max() if not on_freq.empty else 0} starts. "
        "Lighter bars = more starts, darker = fewer starts. Quickly see patterns of usage."
    )
else:
    st.info("No On/Off data for this device.")

# ----------------------
# 3. Failure Analytics
# ----------------------
st.subheader("3️ Failure Analytics")
if not fail_filtered_by_month.empty:
    fail_counts = fail_filtered_by_month.groupby("failure_type").size().reset_index(name="count")
    total_failures = fail_counts["count"].sum()
    
    fig_fail = px.treemap(fail_counts, path=["failure_type"], values="count",
                          color="count", color_continuous_scale="Reds",
                          title="Failure Type Distribution")
    st.plotly_chart(fig_fail, use_container_width=True)
    st.caption(
        f"This device had {total_failures} failures in the selected period. "
        "Largest and darkest rectangles = most frequent failure type. "
        "This helps identify common issues for the device."
    )
else:
    st.info("No failures recorded for this device.")

# ----------------------
# 4. Resting Time Between OFF → Next ON by Month
# ----------------------
st.subheader("4️ Resting Time Between Cycles")
if not onoff_filtered.empty:
    onoff_filtered = onoff_filtered.sort_values("timestamp")
    
    # Compute resting time between OFF → next ON
    rest_list = []
    previous_off_time = None
    for idx, row in onoff_filtered.iterrows():
        if row["on_off_status"] == "OFF":
            previous_off_time = row["timestamp"]
        elif row["on_off_status"] == "ON" and previous_off_time is not None:
            delta = (row["timestamp"] - previous_off_time).total_seconds()/60  # minutes
            rest_list.append({"timestamp": row["timestamp"], "resting_minutes": delta})
            previous_off_time = None

    rest_df = pd.DataFrame(rest_list)
    if not rest_df.empty:
        # Extract month for grouping
        rest_df["month"] = rest_df["timestamp"].dt.to_period("M").astype(str)
        rest_df = rest_df[rest_df["month"].isin(selected_months)]
        
        fig_rest = px.box(rest_df, x="month", y="resting_minutes",
                          points="all", color_discrete_sequence=["skyblue"],
                          title="Distribution of Resting Time Between OFF → Next ON")
        fig_rest.update_layout(xaxis_title="Month", yaxis_title="Resting Time (minutes)")
        st.plotly_chart(fig_rest, use_container_width=True)
        
        monthly_median = rest_df.groupby("month")["resting_minutes"].median().to_dict()
        median_text = ", ".join([f"{m}: {int(median)} min" for m, median in monthly_median.items()])
        
        st.caption(
            f"Median resting times per month: {median_text}. "
            "Shows how much rest the device gets between OFF → next ON. Longer boxes or higher medians = more rest; shorter boxes = frequent use."
        )
    else:
        st.info("Not enough OFF → ON transitions to compute resting time.")
else:
    st.info("No On/Off data for this device.")

# ----------------------
# 5. Runtime / Water Yield / Power Usage
# ----------------------
st.subheader("5️ Runtime / Water Yield / Power Usage")
if not monthly_filtered.empty:
    monthly_filtered_sorted = monthly_filtered.sort_values("month")
    
    # Convert month numbers to month names
    monthly_filtered_sorted["month_name"] = pd.to_datetime(monthly_filtered_sorted["month"].astype(str), format="%Y-%m").dt.strftime("%b %Y")
    
    fig_runtime = go.Figure()
    
    # Runtime bars
    fig_runtime.add_trace(go.Bar(
        x=monthly_filtered_sorted["month_name"],
        y=monthly_filtered_sorted["runtime_hours"],
        name="Runtime (hrs)",
        marker_color="royalblue",
        yaxis="y1"
    ))
    
    # Water Yield line
    fig_runtime.add_trace(go.Scatter(
        x=monthly_filtered_sorted["month_name"],
        y=monthly_filtered_sorted["water_yield_liters"],
        mode="lines+markers",
        name="Water Yield (L)",
        line=dict(color="green"),
        yaxis="y2"
    ))
    
    # Power Consumed line
    fig_runtime.add_trace(go.Scatter(
        x=monthly_filtered_sorted["month_name"],
        y=monthly_filtered_sorted["power_consumed_KVA"],
        mode="lines+markers",
        name="Power Consumed (kVA)",
        line=dict(color="orange"),
        yaxis="y3"
    ))
    
    # Layout for triple-axis
    fig_runtime.update_layout(
        title="Monthly Device Usage Metrics",
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(title="Runtime (hrs)", side="left"),
        yaxis2=dict(title="Water Yield (L)", overlaying="y", side="right"),
        yaxis3=dict(title="Power Consumed (kVA)", overlaying="y", side="right", position=1.1),
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    runtime_total = monthly_filtered_sorted["runtime_hours"].sum()
    water_total = monthly_filtered_sorted["water_yield_liters"].sum()
    power_total = monthly_filtered_sorted["power_consumed_KVA"].sum()
    
    st.plotly_chart(fig_runtime, use_container_width=True)
    st.caption(
        f"In selected month(s): total runtime = {runtime_total:.1f} hrs, "
        f"total water yielded = {water_total:.1f} L, total power consumed = {power_total:.1f} kVA. "
        "Blue bars = runtime, Green line = water yield, Orange line = power. Helps measure efficiency and productivity of this device."
    )
else:
    st.info("No monthly usage data available for this device.")

# ----------------------
st.markdown("---")
st.markdown("📌 Select different UID or month from the sidebar to explore other devices.")