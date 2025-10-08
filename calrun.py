import pandas as pd

# Load the processed CSV
event_logs = pd.read_csv("EL_with_mode_onoff_failure.csv", parse_dates=["created_at", "updated_at"])

# Ensure data is sorted by UID and timestamp
event_logs.sort_values(by=["uid", "created_at"], inplace=True)

# Initialize a runtime column
event_logs["runtime_minutes"] = 0

# Calculate runtime per UID
for uid, group in event_logs.groupby("uid"):
    group = group.reset_index()
    for i in range(1, len(group)):
        # Only count duration if previous status was ON
        if group.loc[i-1, "on_off_status"] == "ON":
            delta = (group.loc[i, "created_at"] - group.loc[i-1, "created_at"]).total_seconds() / 60
            event_logs.loc[group.loc[i, "index"], "runtime_minutes"] = delta

# Aggregate total runtime per UID
runtime_summary = event_logs.groupby("uid")["runtime_minutes"].sum().reset_index()
runtime_summary.rename(columns={"runtime_minutes": "total_runtime_minutes"}, inplace=True)

# Preview
print(runtime_summary.head(10))

# Save for further analysis
runtime_summary.to_csv("EL_runtime_summary_minutes.csv", index=False)