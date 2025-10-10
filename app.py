import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

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
total_runtime = monthly_filtered["runtime_hours"].sum()
total_water = monthly_filtered["water_yield_liters"].sum()
total_power = monthly_filtered["power_consumed_KVA"].sum()
total_failures = len(fail_filtered)

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
fig_mode = px.pie(mode_counts, names="mode", values="count",
                  color="mode", color_discrete_map={"REMOTE":"blue","MANUAL":"orange"},
                  hole=0.4, title="Mode Distribution")
st.plotly_chart(fig_mode, use_container_width=True)
st.caption(
    "Pie chart shows the proportion of time the device operated in REMOTE (blue) vs MANUAL (orange) modes. "
    "This helps understand which mode is dominant for this device."
)

# ----------------------
# 2. On/Off Cycles - Frequency & Patterns with Plain-Language Caption
# ----------------------
st.subheader("2️⃣ Device Start/Stop Patterns Throughout Months")
if not onoff_filtered.empty:
    onoff_filtered["timestamp"] = pd.to_datetime(onoff_filtered["created_at"])
    onoff_filtered["date"] = onoff_filtered["timestamp"].dt.date
    onoff_filtered["month"] = onoff_filtered["timestamp"].dt.to_period("M").astype(str)

    # Aggregate frequency of ON events per day
    on_freq = onoff_filtered[onoff_filtered["on_off_status"]=="ON"].groupby(["month","date"]).size().reset_index(name="count")

    # Use a heatmap-style bar chart to show frequency by day and month
    fig_onoff = px.bar(
        on_freq,
        x="date",
        y="count",
        color="count",
        animation_frame="month",
        color_continuous_scale="Viridis",
        title="Daily Frequency of Device Start Events"
    )
    fig_onoff.update_layout(
        xaxis_title="Date",
        yaxis_title="Number of Starts",
        coloraxis_colorbar=dict(title="Start Count")
    )
    st.plotly_chart(fig_onoff, use_container_width=True)
    
    st.caption(
        "This chart shows when the device was started each day. "
        "Colors indicate the number of starts: lighter color = more starts, darker color = fewer starts. "
        "Use the month selector (top-right) to view daily patterns month by month. "
        "This helps see periods of high activity and periods when the device was mostly idle."
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
                          title="Failure Type Distribution")
    st.plotly_chart(fig_fail, use_container_width=True)
    st.caption(
        "This treemap shows which failures are most common." "Bigger and darker rectangles = more recurring problems."
        "Hover on each block to see the count. This helps prioritize maintenance."
    )
else:
    st.info("No failures recorded for this device.")

# ----------------------
# 4. Resting Time Between OFF → Next ON by Month
# ----------------------
st.subheader("4️⃣ Resting Time Between OFF → Next ON by Month")

if not onoff_filtered.empty:
    onoff_filtered = onoff_filtered.sort_values("timestamp")
    
    # Compute resting time between OFF → next ON
    rest_list = []
    previous_off_time = None
    for idx, row in onoff_filtered.iterrows():
        if row["on_off_status"] == "OFF":
            previous_off_time = row["timestamp"]
        elif row["on_off_status"] == "ON" and previous_off_time is not None:
            delta = (row["timestamp"] - previous_off_time).total_seconds() / 60  # minutes
            rest_list.append({"timestamp": row["timestamp"], "resting_minutes": delta})
            previous_off_time = None

    rest_df = pd.DataFrame(rest_list)
    
    if not rest_df.empty:
        # Extract month for grouping
        rest_df["month"] = rest_df["timestamp"].dt.to_period("M").astype(str)
        
        # Violin + strip plot to show distribution and individual resting times
        fig_rest = px.violin(
            rest_df,
            x="month",
            y="resting_minutes",
            box=True,          # draw box inside violin
            points="all",      # show all points
            color="month",
            title="Distribution of Resting Time Between OFF → Next ON by Month",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_rest.update_layout(
            xaxis_title="Month",
            yaxis_title="Resting Time (minutes)",
            showlegend=False
        )
        st.plotly_chart(fig_rest, use_container_width=True)
        st.caption(
            "Each violin shows how much resting time (in minutes) the device had between being turned OFF and the next ON, for that month. "
            "The width indicates frequency: wider areas = more devices/times had that rest. "
            "Dots show individual rest times. This helps see if the device is getting enough rest or being started too frequently."
        )
    else:
        st.info("Not enough OFF → ON transitions to compute resting time.")
else:
    st.info("No On/Off data for this device.")

# ----------------------
# 5. Runtime / Water Yield / Power Usage - Triple comparison
# ----------------------
st.subheader("5️ Device Efficiency Metrics per Month")

if not monthly_filtered.empty:
    monthly_filtered_sorted = monthly_filtered.sort_values("month")
    monthly_filtered_sorted["month_name"] = pd.to_datetime(monthly_filtered_sorted["month"].astype(str), format="%Y-%m").dt.strftime("%b %Y")

    fig_efficiency = go.Figure()

    # Add bars for Runtime
    fig_efficiency.add_trace(go.Bar(
        x=monthly_filtered_sorted["month_name"],
        y=monthly_filtered_sorted["runtime_hours"],
        name="Runtime (hrs)",
        marker_color="royalblue",
        yaxis="y1"
    ))

    # Add bars for Water Yield
    fig_efficiency.add_trace(go.Bar(
        x=monthly_filtered_sorted["month_name"],
        y=monthly_filtered_sorted["water_yield_liters"],
        name="Water Yield (L)",
        marker_color="green",
        yaxis="y2"
    ))

    # Add bars for Power Consumed
    fig_efficiency.add_trace(go.Bar(
        x=monthly_filtered_sorted["month_name"],
        y=monthly_filtered_sorted["power_consumed_KVA"],
        name="Power Consumed (kVA)",
        marker_color="orange",
        yaxis="y3"
    ))

    # Layout with three y-axes
    fig_efficiency.update_layout(
        title="Monthly Device Efficiency Metrics",
        xaxis=dict(title="Month", tickangle=-45),
        yaxis=dict(
            title="Runtime (hrs)",
            side="left",
            showgrid=False,
            position=0.0
        ),
        yaxis2=dict(
            title="Water Yield (L)",
            side="right",
            overlaying="y",
            showgrid=False,
            position=1.0
        ),
        yaxis3=dict(
            title="Power Consumed (kVA)",
            side="right",
            overlaying="y",
            anchor="free",
            position=0.95,
            showgrid=False
        ),
        barmode='group',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    st.plotly_chart(fig_efficiency, use_container_width=True)
    st.caption(
        "Grouped bars per month show three metrics simultaneously:\n"
        "• Blue = Runtime (hours)\n"
        "• Green = Water Yield (Liters)\n"
        "• Orange = Power Consumed (kVA)\n"
        "Interpretation: Devices that produce more water yield with lower runtime and power are more efficient. "
        "Use the bar heights to compare performance month-to-month."
    )
else:
    st.info("No monthly usage data available for this device.")
# ----------------------
st.markdown("---")
st.markdown("📌 Select different UID or month from the sidebar to explore other devices.")
