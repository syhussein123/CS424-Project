from pathlib import Path
import pandas as pd

root = Path(__file__).resolve().parent
filename = root / "data" / "raw" / "a2_commute_data.csv"

df = pd.read_csv(filename, dtype=str)

# Remove stray spaces from the start/end of every column name
df.columns = df.columns.str.strip()

renameHeader = {
    "Timestamp": "timestamp",
    "What date are you reporting for?": "date",
    "What day of the week is that?": "day_of_week",
    "What time did you leave your starting point?": "depart_time",
    "What time did you arrive at UIC ?": "arrival_time",
    "How many minutes was your total commute? (numeric)": "duration_minutes",
    "What is the distance in miles from your starting point?": "distance_miles",
    "What was your primary mode of transportation today?": "mode_of_transportation",
    "What was the weather like during your commute?": "weather",
    "What is your starting location ?": "location",
}


df = df.rename(columns=renameHeader)
print(df.columns.tolist()) # comment out later

df = df.drop(columns=["timestamp"])

df = df.apply(lambda col: col.str.strip()) #removes leading and trailing whitespace from all columns


# convert date and time columns to proper types
df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")
for col in ["depart_time", "arrival_time"]:
    df[col] = pd.to_datetime(df[col], format="%I:%M:%S %p", errors="coerce").dt.time

# Numbers: strip any text like "10 miles", then convert
for col in ["duration_minutes", "distance_miles"]:
    df[col] = pd.to_numeric(df[col].str.replace(r"[^0-9.]", "", regex=True), errors="coerce")



print(df["location"].value_counts(dropna=False)) #comment out later

#standardizing the location column to match the lookup table
lookup = pd.read_csv(root / "data" / "lookups" / "locations.csv")

df["location_key"] = df["location"].str.strip().str.lower()
df = df.merge(lookup, how="left", left_on="location_key", right_on="raw_value")
df = df.drop(columns=["location_key", "raw_value"])

# show anything the lookup doesn't cover yet
missing = df.loc[df["location_clean"].isna(), "location"].unique()
if len(missing):
    print("Add these to locations.csv:", list(missing))



#addign respondent id labels 
df.insert(0, "respondent_id", [f"R{i}" for i in range(1, len(df) + 1)])


#raining boolean
df["is_rainy"] = df["weather"].str.lower().isin(["raining", "rain", "storm",])

#near uic column: 
df["near_uic"] = df["distance_miles"] <= 5

#duration buckets: 
df["duration_bucket"] = pd.cut(
    df["duration_minutes"],
    bins=[0, 15, 30, 45, 60, 75, 90, float("inf")],
    labels=["0-15", "15-30", "30-45", "45-60", "60-75", "75-90", "90+"],
    right=False,
)


#some more standardization because of the car mixup and the weather mixups 
# --- Standardize mode and weather ---

modeMap = {
    "car (alone)": "Car",
    "car": "Car",
    "carpool": "Carpool",
    "train": "Train",
    "bus": "Bus",
    "walk": "Walk",
    "bicycle": "Bike",
    "bike": "Bike",
}

weatherMap = {
    "sunny": "Sunny",
    "clear": "Sunny",
    "cloudy": "Cloudy",
    "raining": "Raining",
    "rain": "Raining",
}

df["mode_of_transportation"] = df["mode_of_transportation"].str.lower().map(modeMap)
df["weather"] = df["weather"].str.lower().map(weatherMap)

# show anything the maps don't cover yet
for col in ["mode_of_transportation", "weather"]:
    if df[col].isna().any():
        print(f"Unmapped values in {col}: check the map above")
        
#this just creates a new file with the cleaned data
out_dir = root / "data" / "processed"
out_dir.mkdir(parents=True, exist_ok=True)   # creates the folder if it doesn't exist

df.to_csv(out_dir / "commutes_clean.csv", index=False)
print(f"Saved {len(df)} rows to {out_dir / 'commutes_clean.csv'}")