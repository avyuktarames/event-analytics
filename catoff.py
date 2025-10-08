import pandas as pd
import numpy as np

# Load CSV with mode column from Step 2
event_logs = pd.read_csv("EL_with_mode.csv", parse_dates=["created_at", "updated_at"])

# Function to detect ON/OFF status
def detect_on_off(message):
    msg = str(message).lower()
    if "motor started" in msg:
        return "ON"
    elif "motor stopped" in msg:
        return "OFF"
    else:
        return np.nan

# Apply function
event_logs["on_off_status"] = event_logs["message"].apply(detect_on_off)

# Sort by UID and timestamp to get chronological order
event_logs.sort_values(by=["uid", "created_at"], inplace=True)

# Optional: create a numeric column to calculate ON/OFF cycles later
event_logs["on_off_flag"] = event_logs["on_off_status"].map({"ON": 1, "OFF": 0})

# Preview
print(event_logs[["uid", "created_at", "mode", "on_off_status"]].head(30))

# Save to CSV for next steps
event_logs.to_csv("EL_with_mode_onoff.csv", index=False)