from pathlib import Path
import sys
import pandas as pd
import altair as alt
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import json 

HERE = Path(__file__).resolve().parent      # .../source-code
ROOT = HERE.parent                          
CSV_PATH = ROOT / "data" / "processed" / "commutes_clean.csv"
COORDS = ROOT / "data" / "lookups" / "location_coords.csv"
OUT = ROOT / "dashboard.html"
HIGHWAYS = ROOT / "data" / "lookups" / "highways.geojson"

USE_BASEMAP = True          # False = plain lat/lon dots (no internet needed)
MAP_W, MAP_H = 460, 400
MAP_SCALE = 24000
MAP_CENTER = [-88.03, 41.87]   # [lon, lat] of the middle of the map
NEARBY_COUNTIES = [17031, 17043, 17089, 17097, 17111, 17197, 17093, 17037, 17007, 17091, 17063]
# Cook, DuPage, Kane, Lake, McHenry, Will, Kendall, DeKalb, Boone, Kankakee, Grundy
UIC = (41.8708, -87.6505)   # destination marker
OFFSET = 0.05               # degrees (~1.4 mi) of random spread so trips from one origin don't stack
CLUSTER_COLORS = ["#1b9e77", "#d95f02", "#7570b3", "#e7298a",
                  "#66a61e", "#e6ab02", "#a6761d", "#666666"]   # Dark2, one per cluster id 0-7
TRIP_MAP_W, TRIP_MAP_H = 640, 560   # bigger trip-level map so individual dots are easier to hover
TRIP_MAP_SCALE = 4000              # keeps about the same area in view as MAP_SCALE at the larger size

#load data
if not CSV_PATH.exists():
    sys.exit(f"Could not find {CSV_PATH}")
df = pd.read_csv(CSV_PATH)

#coords
if not COORDS.exists():
    sys.exit(f"Could not find {COORDS}")
coords = pd.read_csv(COORDS)

#any location in the data that isn't in the lookup yet (e.g. after a new data sample)
new_locs = sorted(set(df["location_clean"].dropna()) - set(coords["location_clean"]))
if new_locs:
    print("NOT IN lookup file, add them to location_coords.csv:", new_locs)

missing = coords[coords["lat"].isna() | coords["lon"].isna()]["location_clean"].tolist()
if missing:
    print("No coordinates (left off the map, still in other views):", missing)

df = df.merge(coords, on="location_clean", how="left")


# =====================================================================
# EXTRA CREDIT HOOK 1 (data side): K-means
# Whoever does the extra credit edits this function.
# Plan: static HTML can't run sklearn live, so PRECOMPUTE clusterings for
# k = 2..8 and add one column per k (cluster_k2 ... cluster_k8). The slider
# then just chooses which column to color by.
#   - features: distance_miles, duration_minutes, depart hour, plus one-hot
#     weather / mode / day. Scale everything (StandardScaler) first.
#   - for k in range(2, 9): df[f"cluster_k{k}"] = KMeans(k, n_init=10,
#       random_state=0).fit_predict(X).astype(str)
#   - return the dataframe with the new columns.
# =====================================================================
def add_cluster_columns(df):
    depart = pd.to_datetime(df["depart_time"], format="%H:%M:%S")
    X_num = pd.DataFrame({
        "distance_miles": df["distance_miles"],
        "duration_minutes": df["duration_minutes"],
        "depart_hour": depart.dt.hour + depart.dt.minute / 60,
    })
    X_cat = pd.get_dummies(df[["weather", "mode_of_transportation", "day_of_week"]], dtype=float)
    X = StandardScaler().fit_transform(pd.concat([X_num, X_cat], axis=1))
    for k in range(2, 9):
        labels = KMeans(n_clusters=k, n_init=10, random_state=0).fit_predict(X)
        df[f"cluster_k{k}"] = labels.astype(str)
    return df


def add_map_offsets(df):
    # one dot per trip; a seeded random nudge keeps the dots from stacking on one origin
    rng = np.random.default_rng(0)
    df["lat_plot"] = df["lat"] + rng.uniform(-OFFSET, OFFSET, len(df))
    df["lon_plot"] = df["lon"] + rng.uniform(-OFFSET, OFFSET, len(df))
    return df


def build_cluster_summary(df):
    # one row per (k, cluster) for the cluster panel; precomputed so the page stays static
    rows = []
    for k in range(2, 9):
        for cid, sub in df.groupby(f"cluster_k{k}"):
            rows.append({
                "k": k,
                "cluster": cid,
                "trips": len(sub),
                "avg_duration": round(sub["duration_minutes"].mean(), 1),
                "avg_distance": round(sub["distance_miles"].mean(), 1),
                "top_mode": sub["mode_of_transportation"].mode().iat[0],
                "top_weather": sub["weather"].mode().iat[0],
            })
    return pd.DataFrame(rows)


df = add_cluster_columns(df)
df = add_map_offsets(df)
cluster_summary = build_cluster_summary(df)
df_map = df.dropna(subset=["lat", "lon"])


# =====================================================================
# EXTRA CREDIT 2 (view side)
# Replace the placeholder with the real panel. Suggested design:
#   k_pick = alt.param(name="k_pick", value=4,
#                      bind=alt.binding_range(min=2, max=8, step=1, name="Clusters (k): "))
#   chart.add_params(k_pick).transform_calculate(
#       cluster="datum['cluster_k' + k_pick]")   # then color='cluster:N'
# Show clusters on the map and/or scatter, and add a small table or bars
# describing each cluster (avg duration, distance, common weather/mode).
# =====================================================================
def cluster_panel(summary):
    return (alt.Chart(summary).transform_filter("datum.k == k_pick")
            .mark_bar()
            .encode(x=alt.X("cluster:N", title="Cluster", sort=None),
                    y=alt.Y("avg_duration:Q", title="Avg commute (Minutes)"),
                    color=alt.Color("cluster:N", legend=None, scale=CLUSTER_SCALE),
                    tooltip=[alt.Tooltip("cluster:N", title="Cluster"),
                             alt.Tooltip("trips:Q", title="Trips"),
                             alt.Tooltip("avg_duration:Q", title="Avg (min)", format=".1f"),
                             alt.Tooltip("avg_distance:Q", title="Avg distance (mi)", format=".1f"),
                             alt.Tooltip("top_mode:N", title="Most common mode"),
                             alt.Tooltip("top_weather:N", title="Most common weather")])
            .properties(title="Clusters at the chosen k: average commute per cluster",
                        width=480, height=340))


# standardized color, day, weather, and modes
days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
modes = df["mode_of_transportation"].dropna().unique().tolist()
weathers = sorted(df["weather"].dropna().unique().tolist())
palette = ["#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
           "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52"]
mode_scale = alt.Scale(domain=modes, range=palette[:len(modes)])

#shared state
weather_pick = alt.param(name="weather_pick", value="All")
day_pick = alt.param(name="day_pick", value="All")
map_select = alt.selection_point(fields=["location_clean"])           # click map (shift = several)
mode_select = alt.selection_point(fields=["mode_of_transportation"], bind="legend")
brush = alt.selection_interval(encodings=["x"])                       # drag a distance range
k_pick = alt.param(name="k_pick", value=4,                            # K-means slider (extra credit)
                   bind=alt.binding_range(min=2, max=8, step=1, name="Clusters (k): "))
CLUSTER_SCALE = alt.Scale(domain=[str(i) for i in range(8)], range=CLUSTER_COLORS)  # same color per id at any k

WEATHER_OK = "(weather_pick == 'All' || datum.weather == weather_pick)"
DAY_OK = "(day_pick == 'All' || datum.day_of_week == day_pick)"
FILTER = f"{WEATHER_OK} && {DAY_OK}"

#where people commute from map
points = (alt.Chart(df_map).transform_filter(FILTER).transform_filter(mode_select)
          .mark_circle(stroke="white", strokeWidth=1)
          .encode(longitude="lon:Q", latitude="lat:Q", detail="location_clean:N",
                  size=alt.Size("count():Q", title="Trips", legend=None, scale=alt.Scale(range=[70, 900])),
                  color=alt.Color("mean(duration_minutes):Q", title="Avg minutes",
                                  scale=alt.Scale(scheme="orangered")),
                  opacity=alt.condition(map_select, alt.value(0.92), alt.value(0.3)),
                  tooltip=[alt.Tooltip("location_clean:N", title="Origin"),
                           alt.Tooltip("count():Q", title="Trips"),
                           alt.Tooltip("mean(duration_minutes):Q", title="Avg (min)", format=".1f")])
          .add_params(map_select))

# one dot per trip, colored by the cluster at the chosen k (extra credit); bigger than the origin map so trips are easier to hover
trip_points = (alt.Chart(df_map).transform_filter(FILTER).transform_filter(mode_select)
          .transform_calculate(cluster="datum['cluster_k' + k_pick]")
          .mark_circle(stroke="white", strokeWidth=0.8, size=110)
          .encode(longitude="lon_plot:Q", latitude="lat_plot:Q",
                  color=alt.Color("cluster:N", title="Cluster", scale=CLUSTER_SCALE),
                  tooltip=[alt.Tooltip("location_clean:N", title="Origin"),
                           alt.Tooltip("day_of_week:N", title="Day"),
                           alt.Tooltip("weather:N", title="Weather"),
                           alt.Tooltip("mode_of_transportation:N", title="Mode"),
                           alt.Tooltip("distance_miles:Q", title="Distance (mi)"),
                           alt.Tooltip("duration_minutes:Q", title="Duration (min)"),
                           alt.Tooltip("cluster:N", title="Cluster")])
          .add_params(k_pick))

uic = (alt.Chart(pd.DataFrame({"lat": [UIC[0]], "lon": [UIC[1]], "name": ["UIC (destination)"]}))
       .mark_point(shape="diamond", size=200, filled=True, color="#111827", stroke="white", strokeWidth=1.5)
       .encode(longitude="lon:Q", latitude="lat:Q", tooltip="name:N"))

basemap_layers = []
with open(HIGHWAYS) as f:
    highway_features = json.load(f)["features"]
road_chart = alt.Chart(alt.Data(values=highway_features)).encode(shape="geometry:G")
minor_roads = (road_chart.transform_filter("datum.properties.kind == 'road'")
               .mark_geoshape(fill=None, stroke="#cbd5e1", strokeWidth=0.8))
interstates = (road_chart.transform_filter("datum.properties.kind == 'interstate'")
               .mark_geoshape(fill=None, stroke="#6b7280", strokeWidth=1.6))
basemap_layers = basemap_layers + [minor_roads, interstates]

if USE_BASEMAP:
    from vega_datasets import data as vdata
    counties = alt.topo_feature(vdata.us_10m.url, "counties")
    basemap = (alt.Chart(counties)
               .mark_geoshape(fill="#e5e9f0", stroke="white", strokeWidth=1.2, clip=True)
               .transform_filter(f"indexof({NEARBY_COUNTIES}, datum.id) >= 0"))
    basemap_layers = [basemap] + basemap_layers

map_chart = (alt.layer(*basemap_layers, points, uic)
             .project(type="mercator", scale=MAP_SCALE, center=MAP_CENTER,
                      translate=[MAP_W / 2, MAP_H / 2])      # <-- this is the actual fix
             .properties(title="Where trips start (click origins; size = trips, color = avg time)",
                         width=MAP_W, height=MAP_H))

# trip-level map: same basemap and destination, larger so individual trips are easier to hover
trip_map = (alt.layer(*basemap_layers, trip_points, uic)
            .project(type="mercator", scale=TRIP_MAP_SCALE, center=MAP_CENTER,
                     translate=[TRIP_MAP_W / 2, TRIP_MAP_H / 2])
            .properties(title="Each dot is one trip (color = cluster at the chosen k)",
                        width=TRIP_MAP_W, height=TRIP_MAP_H))

#distance vs duration scatterplot
scatter = (alt.Chart(df).transform_filter(FILTER).transform_filter(map_select)
           .mark_circle(size=64)
           .encode(x=alt.X("distance_miles:Q", title="Distance (Miles)",
                           axis=alt.Axis(values=list(range(0, 50, 5)))),
                   y=alt.Y("duration_minutes:Q", title="Commute Time (Minutes)"),
                   color=alt.Color("mode_of_transportation:N", title="Transport Mode", scale=mode_scale),
                   opacity=alt.condition(brush & mode_select, alt.value(0.8), alt.value(0.1)),
                   tooltip=[alt.Tooltip("day_of_week:N", title="Day"),
                            alt.Tooltip("weather:N", title="Weather"),
                            alt.Tooltip("location_clean:N", title="Origin"),
                            alt.Tooltip("mode_of_transportation:N", title="Mode"),
                            alt.Tooltip("distance_miles:Q", title="Distance (mi)"),
                            alt.Tooltip("duration_minutes:Q", title="Duration (min)")])
           .add_params(brush, mode_select, weather_pick, day_pick)
           .properties(title="Drag a distance range; click legend to isolate a mode",
                       width=430, height=360))

# day of the week bar chart
bars = (alt.Chart(df).transform_filter(WEATHER_OK).transform_filter(map_select)
        .transform_filter(brush).transform_filter(mode_select)
        .mark_bar()
        .encode(x=alt.X("day_of_week:N", sort=days_order, title="Day of Week"),
                xOffset=alt.XOffset("mode_of_transportation:N", sort=modes),
                y=alt.Y("mean(duration_minutes):Q", title="Average Commute (Minutes)"),
                color=alt.Color("mode_of_transportation:N", legend=None, scale=mode_scale),
                opacity=alt.condition(DAY_OK, alt.value(1), alt.value(0.3)),
                tooltip=[alt.Tooltip("day_of_week:N", title="Day"),
                         alt.Tooltip("mode_of_transportation:N", title="Mode"),
                         alt.Tooltip("mean(duration_minutes):Q", title="Avg (min)", format=".1f"),
                         alt.Tooltip("count():Q", title="Trips")])
        .properties(title="Average commute by day and mode (Day dropdown highlights)",
                    width=430, height=300))

# mode average and spread for the current selection
sbase = (alt.Chart(df).transform_filter(FILTER).transform_filter(map_select)
         .transform_filter(brush).transform_filter(mode_select))
sbars = sbase.mark_bar(opacity=0.85).encode(
    y=alt.Y("mode_of_transportation:N", title=None, scale=alt.Scale(domain=modes)),
    x=alt.X("mean(duration_minutes):Q", title="Avg Commute Time (Minutes), error bar = ±1 SD"),
    color=alt.Color("mode_of_transportation:N", legend=None, scale=mode_scale),
    tooltip=[alt.Tooltip("mode_of_transportation:N", title="Mode"),
             alt.Tooltip("mean(duration_minutes):Q", title="Mean (min)", format=".1f"),
             alt.Tooltip("stdev(duration_minutes):Q", title="SD (min)", format=".1f"),
             alt.Tooltip("count():Q", title="Trips")])
sspread = sbase.mark_errorbar(extent="stdev", color="black").encode(
    y=alt.Y("mode_of_transportation:N", scale=alt.Scale(domain=modes)),
    x=alt.X("duration_minutes:Q"))
summary = (sbars + sspread).properties(
    title="Selected trips: average and spread by mode", width=430, height=300)

# UI assembling
top = alt.hconcat(map_chart, scatter).resolve_scale(color="independent", size="independent")
bottom = alt.hconcat(bars, summary).resolve_scale(color="independent")

dashboard = (
    alt.vconcat(top, bottom, alt.hconcat(cluster_panel(cluster_summary), trip_map))
    .resolve_scale(color="independent", size="independent")
    .configure(background="#ffffff")
    .configure_view(stroke=None)
    .configure_title(anchor="start", fontSize=14, color="#1f2937", offset=10)
    .configure_axis(labelColor="#4b5563", titleColor="#374151", gridColor="#eef0f4",
                    domainColor="#d1d5db", tickColor="#d1d5db")
    .configure_legend(labelColor="#4b5563", titleColor="#374151")
)

import json

def options_html(values):
    return "".join(f'<option value="{v}">{v}</option>' for v in ["All"] + values)

HTML = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>What shapes a commute to campus?</title>
<script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
<style>
  body {{ background:#be95c4; font-family:'Segoe UI', system-ui, sans-serif; margin:0; padding:24px; }}
  .card {{ background:#fff; border-radius:14px; padding:22px 26px;
           box-shadow:0 2px 14px rgba(15,23,42,.08); width:fit-content; margin:0 auto; }}
  h1 {{ margin:0 0 4px; font-size:26px; color:#111827; }}
  .sub {{ margin:0 0 16px; font-size:13px; color:#6b7280; }}
  .filters {{ display:flex; gap:28px; align-items:center; padding:12px 16px; margin-bottom:18px;
              background:#f3f4f8; border:1px solid #e5e7eb; border-radius:10px; }}
  .filters label {{ font-weight:600; color:#374151; font-size:14px; display:flex; align-items:center; gap:8px; }}
  .filters select {{ padding:6px 12px; border:1px solid #cbd5e1; border-radius:6px;
                     background:#fff; font-size:14px; }}
</style>
</head>
<body>
<div class="card">
  <h1>What shapes a commute to campus?</h1>
  <p class="sub">Pick a weather or day, click map origins, drag a distance range on the scatter, or click the legend to isolate a mode. Use the cluster slider to color trips on the map.</p>
  <div class="filters">
    <label>Weather <select id="weather">{options_html(weathers)}</select></label>
    <label>Day <select id="day">{options_html(days_order)}</select></label>
  </div>
  <div id="vis"></div>
</div>
<script>
  const spec = {dashboard.to_json()};
  vegaEmbed('#vis', spec, {{actions:false}}).then(res => {{
    const view = res.view;
    document.getElementById('weather').addEventListener('change', e => {{
      view.signal('weather_pick', e.target.value).run();
    }});
    document.getElementById('day').addEventListener('change', e => {{
      view.signal('day_pick', e.target.value).run();
    }});
  }});
</script>
</body>
</html>"""

OUT.write_text(HTML, encoding="utf-8")
print(f"Saved {OUT}")