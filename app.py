import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
fail_filtered = fail_data[(fail_data["uid"] == selected_uid) &
                          (fail_data["created_at"].dt.to_period("M").astype(str).isin(selected_months))]
rest_filtered = rest_data[(rest_data["uid"] == selected_uid)]
monthly_filtered = monthly_data[(monthly_data["uid"] == selected_uid) &
                                (monthly_data["month"].isin(selected_months))]

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
# 1. Mode Distribution
# ----------------------
st.subheader("1️ Device Mode Distribution")
mode_counts = mode_filtered["mode"].value_counts().reset_index()
mode_counts.columns = ["mode", "count"]
fig_mode = px.pie(mode_counts, names="mode", values="count",
                  color="mode", color_discrete_map={"REMOTE":"blue","MANUAL":"orange"},
                  hole=0.4, title=f"Mode Distribution for Device {selected_uid}")
st.plotly_chart(fig_mode, use_container_width=True)
st.caption(
    f"Pie chart shows how much time Device {selected_uid} operated in REMOTE (blue) vs MANUAL (orange). "
    f"Total recordings: {mode_counts['count'].sum()}."
)

# ----------------------
# 2. On/Off Cycles
# ----------------------
st.subheader("2️ Start/Stop Frequency and Patterns")
if not onoff_filtered.empty:
    onoff_filtered["timestamp"] = pd.to_datetime(onoff_filtered["created_at"])
    onoff_filtered["date"] = onoff_filtered["timestamp"].dt.date
    on_freq = onoff_filtered[onoff_filtered["on_off_status"]=="ON"].groupby("date").size().reset_index(name="count")
    
    fig_onoff = px.bar(on_freq, x="date", y="count",
                       color="count", color_continuous_scale="Viridis",
                       title=f"Daily Start Events for Device {selected_uid}")
    fig_onoff.update_layout(xaxis_title="Date", yaxis_title="Number of Starts")
    st.plotly_chart(fig_onoff, use_container_width=True)
    st.caption(
        f"Bar chart shows how often Device {selected_uid} was started daily. "
        f"Lighter bars = more starts, darker bars = fewer starts. "
        f"Max starts/day: {on_freq['count'].max()}, Min starts/day: {on_freq['count'].min()}."
    )
else:
    st.info("No On/Off data for this device.")

# ----------------------
# 3. Failure Analytics
# ----------------------
st.subheader("3️ Failure Analytics")
if not fail_filtered.empty:
    fail_counts = fail_filtered.groupby("failure_type").size().reset_index(name="count")
    fig_fail = px.treemap(fail_counts, path=["failure_type"], values="count",
                          color="count", color_continuous_scale="Reds",
                          title=f"Failure Type Distribution for Device {selected_uid}")
    st.plotly_chart(fig_fail, use_container_width=True)
    st.caption(
        f"Treemap shows frequency of failures for Device {selected_uid}. "
        f"Most common: {fail_counts.iloc[fail_counts['count'].idxmax()]['failure_type']} ({fail_counts['count'].max()} times)."
    )
else:
    st.info("No failures recorded for this device.")

# ----------------------
# 4. Resting Time Between OFF → Next ON (Violin Plot)
# ----------------------
st.subheader("4️ Resting Time Between Cycles")
if not onoff_filtered.empty:
    onoff_filtered = onoff_filtered.sort_values("timestamp")
    rest_list = []
    previous_off_time = None
    for idx, row in onoff_filtered.iterrows():
        if row["on_off_status"] == "OFF":
            previous_off_time = row["timestamp"]
        elif row["on_off_status"] == "ON" and previous_off_time is not None:
            delta = (row["timestamp"] - previous_off_time).total_seconds()/60
            rest_list.append({"timestamp": row["timestamp"], "resting_minutes": delta})
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
            f"Violin plot shows resting time between OFF → next ON for Device {selected_uid} per month. "
            f"Longer violins or higher median = more rest between cycles."
        )
    else:
        st.info("Not enough OFF → ON transitions to compute resting time.")
else:
    st.info("No On/Off data for this device.")

# ----------------------
# 5. Runtime / Water Yield / Power Usage (Bubble Chart)
# ----------------------
st.subheader("5️ Efficiency Metrics per Month")
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
        f"Bubble chart shows efficiency of Device {selected_uid} per month. "
        f"X-axis = Runtime hours, Y-axis = Power consumed, Bubble size = Water Yield (L). "
        f"Large bubble + lower power + lower runtime = higher efficiency."
    )
else:
    st.info("No monthly usage data available for this device.")

st.markdown("---")
st.markdown("📌 Use the sidebar to select different UID or month for analysis.")