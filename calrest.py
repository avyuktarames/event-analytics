import pandas as pd

# Load the processed CSV with on/off status and runtime
event_logs = pd.read_csv("EL_with_mode_onoff_failure.csv", parse_dates=["created_at", "updated_at"])
event_logs["resting_minutes"] = 0.0
# Sort by UID and timestamp
event_logs.sort_values(by=["uid", "created_at"], inplace=True)

# Initialize resting time column
event_logs["resting_minutes"] = 0

# Calculate resting time per UID
for uid, group in event_logs.groupby("uid"):
    group = group.reset_index()
    for i in range(1, len(group)):
        # Only count resting if previous status was OFF
        if group.loc[i-1, "on_off_status"] == "OFF":
            delta = (group.loc[i, "created_at"] - group.loc[i-1, "created_at"]).total_seconds() / 60
            event_logs.loc[group.loc[i, "index"], "resting_minutes"] = delta

# Aggregate total resting time per UID
resting_summary = event_logs.groupby("uid")["resting_minutes"].sum().reset_index()
resting_summary.rename(columns={"resting_minutes": "total_resting_minutes"}, inplace=True)

# Preview
print(resting_summary.head(10))

# Save for further analysis
resting_summary.to_csv("EL_resting_summary_minutes.csv", index=False)