from pathlib import Path
import sys
import pandas as pd
import altair as alt

HERE = Path(__file__).resolve().parent      # .../source-code
ROOT = HERE.parent                          
CSV_PATH = ROOT / "data" / "processed" / "commutes_clean.csv"
COORDS = ROOT / "data" / "lookups" / "location_coords.csv"
OUT = ROOT / "dashboard.html"

USE_BASEMAP = True          # False = plain lat/lon dots (no internet needed)
MAP_W, MAP_H = 460, 400
MAP_SCALE = 24000
MAP_CENTER = [-88.03, 41.87]   # [lon, lat] of the middle of the map
NEARBY_COUNTIES = [17031, 17043, 17089, 17097, 17111, 17197, 17093, 17037, 17007, 17091, 17063]
# Cook, DuPage, Kane, Lake, McHenry, Will, Kendall, DeKalb, Boone, Kankakee, Grundy
UIC = (41.8708, -87.6505)   # destination marker

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
    return df


df = add_cluster_columns(df)
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
def cluster_panel():
    t = pd.DataFrame({"t": ["EXTRA CREDIT: K-means cluster panel goes here (see comments in dashboard.py)"]})
    return (alt.Chart(t).mark_text(size=14, color="gray")
            .encode(text="t:N", x=alt.value(450), y=alt.value(30))
            .properties(width=900, height=60))


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

uic = (alt.Chart(pd.DataFrame({"lat": [UIC[0]], "lon": [UIC[1]], "name": ["UIC (destination)"]}))
       .mark_point(shape="diamond", size=200, filled=True, color="#111827", stroke="white", strokeWidth=1.5)
       .encode(longitude="lon:Q", latitude="lat:Q", tooltip="name:N"))

layers = [points, uic]
if USE_BASEMAP:
    from vega_datasets import data as vdata
    counties = alt.topo_feature(vdata.us_10m.url, "counties")
    basemap = (alt.Chart(counties)
               .mark_geoshape(fill="#e5e9f0", stroke="white", strokeWidth=1.2, clip=True)
               .transform_filter(f"indexof({NEARBY_COUNTIES}, datum.id) >= 0"))
    layers = [basemap] + layers

map_chart = (alt.layer(*layers)
             .project(type="mercator", scale=MAP_SCALE, center=MAP_CENTER,
                      translate=[MAP_W / 2, MAP_H / 2])      # <-- this is the actual fix
             .properties(title="Where trips start (click origins; size = trips, color = avg time)",
                         width=MAP_W, height=MAP_H))

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
    alt.vconcat(top, bottom, cluster_panel())
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
  <p class="sub">Pick a weather or day, click map origins, drag a distance range on the scatter, or click the legend to isolate a mode.</p>
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