#calculates no of hours used monthly, water device has yielded, power it has consumed
import pandas as pd
import re
import numpy as np

# Load Event Logs
event_logs = pd.read_csv("EL.csv", parse_dates=["created_at", "updated_at"])
event_logs = event_logs.sort_values(by=["uid", "created_at"]).reset_index(drop=True)

# ------------------------------
# Step 1: Extract runtime_minutes from messages
# ------------------------------
def extract_runtime(msg):
    msg = str(msg)
    match = re.search(r"Total Run Time\s*[:\-]?\s*(\d+\.?\d*)\s*minutes", msg, re.IGNORECASE)
    return float(match.group(1)) if match else 0.0

event_logs["runtime_minutes"] = event_logs["message"].apply(extract_runtime)

# ------------------------------
# Step 2: Extract water_yield_liters from messages
# ------------------------------
def extract_water_yield(msg):
    msg = str(msg)
    match = re.search(r"Water\s*Yield\s*[:\-]?\s*(\d+\.?\d*)", msg, re.IGNORECASE)
    return float(match.group(1)) if match else 0.0

event_logs["water_yield_liters"] = event_logs["message"].apply(extract_water_yield)

# ------------------------------
# Step 3: Extract power_consumed_units in kVA
# ------------------------------
def extract_power_kva(msg):
    msg = str(msg)
    volts = re.findall(r"[RYB]:\s*(\d+\.?\d*)\s*volts", msg, re.IGNORECASE)
    volts = [float(v) for v in volts]
    amps = re.findall(r"[RYB]:\s*(\d+\.?\d*)\s*amps", msg, re.IGNORECASE)
    amps = [float(a) for a in amps]
    if len(volts) == 3 and len(amps) == 3:
        # 3-phase apparent power formula in kVA
        return (np.sqrt(3) * sum(volts)/3 * sum(amps)/3)/1000
    else:
        return 0.0

event_logs["power_consumed_KVA"] = event_logs["message"].apply(extract_power_kva)

# ------------------------------
# Step 4: Extract month
# ------------------------------
event_logs["month"] = event_logs["created_at"].dt.to_period("M").astype(str)

# ------------------------------
# Step 5: Aggregate monthly per device
# ------------------------------
monthly_agg = event_logs.groupby(["uid", "month"]).agg(
    runtime_hours=("runtime_minutes", lambda x: x.sum() / 60),  # convert to hours
    water_yield_liters=("water_yield_liters", "sum"),
    power_consumed_KVA=("power_consumed_KVA", "sum")
).reset_index()

# ------------------------------
# Step 6: Save final CSV
# ------------------------------
monthly_agg.to_csv("monthly_device_usage.csv", index=False)
print("Monthly device usage saved to 'monthly_device_usage.csv'")
print(monthly_agg.head())