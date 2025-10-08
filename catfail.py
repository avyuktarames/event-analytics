import pandas as pd
import numpy as np

# Load the latest processed CSV
event_logs = pd.read_csv("EL_with_mode_onoff.csv", parse_dates=["created_at", "updated_at"])

# Function to detect failures
def detect_failure(message):
    msg = str(message).lower()
    if "overload" in msg:
        return "Overload"
    elif "underload" in msg:
        return "Underload"
    elif "power failed" in msg or "power notification" in msg:
        return "Power Failure"
    elif "maintenance alert" in msg:
        return "Maintenance Alert"
    elif "error" in msg:
        return "Error"
    else:
        return np.nan

# Apply the function
event_logs["failure_type"] = event_logs["message"].apply(detect_failure)

# Preview
print(event_logs[["uid", "created_at", "mode", "on_off_status", "failure_type"]].head(30))

# Save for next steps
event_logs.to_csv("EL_with_mode_onoff_failure.csv", index=False)