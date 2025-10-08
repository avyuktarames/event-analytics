import pandas as pd
import numpy as np

# Load your event logs CSV (already sorted by UID & created_at)
event_logs = pd.read_csv("EL.csv", parse_dates=["created_at", "updated_at"])

# Function to detect mode
def detect_mode(message):
    message = str(message).lower()
    if "remote" in message:
        return "REMOTE"
    elif "manual" in message:
        return "MANUAL"
    else:
        return np.nan

# Apply function
event_logs["mode"] = event_logs["message"].apply(detect_mode)

# Preview the result
print(event_logs[["uid", "created_at", "message", "mode"]].head(20))

# Save to a new CSV for the next steps
event_logs.to_csv("EL_with_mode.csv", index=False)