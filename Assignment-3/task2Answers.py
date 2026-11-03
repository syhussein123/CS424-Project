import pandas as pd

path = "../data/processed/commutes_clean.csv"
modes = ["Car", "Train"]
var = {"Variant A": (10, 20), "Variant B": (30, 40)}
min_trips = 5         # flag any mode with fewer trips than this in a range
tie = 1.0   # minutes; differences smaller than this are flagged as ties

df = pd.read_csv(path)
df = df[df["mode_of_transportation"].isin(modes)].copy()

for variant, (lo, hi) in var.items():
    # Inclusive on both ends. Trips sitting exactly on a boundary are counted,
    # so the brushed range in the interactive version must include them too.
    in_range = df["distance_miles"].between(lo, hi, inclusive="both")
    subset = df[in_range]
    boundary_trips = len(df[df["distance_miles"].isin([lo, hi])])

    stats = (
        subset.groupby("mode_of_transportation")["duration_minutes"]
        .agg(trips="count", mean="mean", sd="std")  # sample SD (ddof=1), same as Vega-Lite stdev
        .reindex(modes)
    )

    print(f"\n{variant}: {lo}-{hi} miles")
    print(stats.round(2).to_string())
    print(f"Trips sitting exactly on {lo} or {hi} miles: {boundary_trips}")

    # Warnings
    for mode in modes:
        if pd.isna(stats.loc[mode, "trips"]) or stats.loc[mode, "trips"] < min_trips:
            print(f"WARNING: {mode} has fewer than {min_trips} trips in this range")

    # Task 1: higher average
    mean_diff = abs(stats.loc["Car", "mean"] - stats.loc["Train", "mean"])
    if mean_diff < tie:
        print(f"Task 1 answer: TIE (difference {mean_diff:.2f} min). Do not use this variant.")
    else:
        winner = stats["mean"].idxmax()
        print(f"Task 1 answer (higher average): {winner}, difference {mean_diff:.2f} min")

    # Task 2: lower SD = more consistent
    sd_diff = abs(stats.loc["Car", "sd"] - stats.loc["Train", "sd"])
    if sd_diff < tie:
        print(f"Task 2 answer: TIE (SD difference {sd_diff:.2f} min). Do not use this variant.")
    else:
        winner = stats["sd"].idxmin()
        print(f"Task 2 answer (more consistent, lower SD): {winner}, SD difference {sd_diff:.2f} min")