import pandas as pd

# --------------------------
# File paths
# --------------------------
utilization_file = "chart_utilization.csv"
water_file = "chart_water_analytics.csv"
output_file = "correl_cleaned.csv"

# --------------------------
# Load utilization data
# --------------------------
util_df = pd.read_csv(utilization_file, parse_dates=["created_at"])
# Select only necessary columns
util_df = util_df[["uid", "total_runtime", "created_at"]]

# --------------------------
# Load water analytics data
# --------------------------
water_df = pd.read_csv(water_file, parse_dates=["created_at"])
# Standardize column names
water_df.rename(columns={
    water_df.columns[1]: "uid",
    water_df.columns[3]: "water_level_below_surface",
    water_df.columns[5]: "created_at"
}, inplace=True)

# Convert negative water levels to positive
water_df["water_level_below_surface"] = water_df["water_level_below_surface"].abs()

# --------------------------
# Merge datasets on uid and nearest previous date
# --------------------------
# Round created_at to date to avoid mismatches due to time
util_df["date"] = util_df["created_at"].dt.date
water_df["date"] = water_df["created_at"].dt.date

# Perform inner merge on uid and date
merged_df = pd.merge(
    util_df,
    water_df,
    on=["uid", "date"],
    how="inner",
    suffixes=("_util", "_water")
)

# Keep only the required columns
merged_df = merged_df[["uid", "total_runtime", "created_at_water", "water_level_below_surface"]]
merged_df.rename(columns={"created_at_water": "created_at"}, inplace=True)

# --------------------------
# Fill nulls with average safely
# --------------------------
merged_df["total_runtime"] = merged_df["total_runtime"].fillna(merged_df["total_runtime"].mean())
merged_df["water_level_below_surface"] = merged_df["water_level_below_surface"].fillna(
    merged_df["water_level_below_surface"].mean()
)

# --------------------------
# Save to CSV
# --------------------------
merged_df.to_csv(output_file, index=False)
print(f"✅ Correlation cleaned data saved to: {output_file}")
print(f"Unique UIDs in merged CSV: {merged_df['uid'].nunique()}")
print(merged_df.head(10))