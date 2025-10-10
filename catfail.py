import pandas as pd
import numpy as np
import re

# Load the latest processed CSV
event_logs = pd.read_csv("EL_with_mode_onoff.csv", parse_dates=["created_at", "updated_at"])

# Define patterns for different failures (case-insensitive)
failure_patterns = {
    "Power Failure": re.compile(r"\bpower failed\b", re.IGNORECASE),
    "Underload/Dryrun": re.compile(r"underload|dryrun", re.IGNORECASE),
    "Overload": re.compile(r"overload", re.IGNORECASE),
    "Maintenance Alert": re.compile(r"maintenance alert", re.IGNORECASE),
    "Error": re.compile(r"\berror\b", re.IGNORECASE),
}

def detect_failure(message):
    msg = str(message)
    for failure_type, pattern in failure_patterns.items():
        if pattern.search(msg):
            return failure_type
    return np.nan

# Apply the function
event_logs["failure_type"] = event_logs["message"].apply(detect_failure)

# Preview the result
print(event_logs[["uid", "created_at", "mode", "on_off_status", "message", "failure_type"]].head(30))

# Save for next steps
event_logs.to_csv("EL_with_mode_onoff_failure.csv", index=False)