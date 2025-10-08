import pandas as pd

# 1. Load the event logs CSV
event_logs = pd.read_csv("EL.csv", parse_dates=["created_at", "updated_at"])

# 2. Sort by UID and created_at to get chronological order per device
event_logs_sorted = event_logs.sort_values(by=["uid", "created_at"]).reset_index(drop=True)

# 3. Optional: Preview
print(event_logs_sorted.head(20))

# 4. Group by UID if you want to prepare for per-device analytics
device_groups = event_logs_sorted.groupby("uid")