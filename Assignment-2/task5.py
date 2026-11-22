import pandas as pd
import altair as alt

df = pd.read_csv("data/processed/commutes_clean.csv")

bins = [0, 15, 30, 45, 60, 75, 90, 200]
labels = ['0-15', '15-30', '30-45', '45-60', '60-75', '75-90', '90+']
df['duration_bucket_str'] = pd.cut(df['duration_minutes'], bins=bins, labels=labels).astype(str)

# Clicking a heatmap cell selects that (weather, duration bucket) combination.
# Shift-click adds more cells. Clicking empty space clears the selection.
cell_select = alt.selection_point(
    fields=['weather', 'duration_bucket_str'],
    name='cell_select'
)

#overall how many commutes fall in each weather x duration cell
heatmap = alt.Chart(df).mark_rect().encode(
    x=alt.X('weather:N', title='Weather'),
    y=alt.Y('duration_bucket_str:O', title='Commute Time (Minutes)', sort=labels),
    color=alt.Color('count():Q', title='Number of People', scale=alt.Scale(scheme='blues')),
    opacity=alt.condition(cell_select, alt.value(1), alt.value(0.35)),
    tooltip=[
        alt.Tooltip('weather:N', title='Weather'),
        alt.Tooltip('duration_bucket_str:O', title='Duration (min)'),
        alt.Tooltip('count():Q', title='People')
    ]
).add_params(
    cell_select
).properties(
    title={"text": "Weather vs Commute Duration",
           "subtitle": "Click a cell to see its trips (shift-click for several)"},
    width=350,
    height=350
)

# the individual trips behind the counts
scatter = alt.Chart(df).mark_circle(size=70).encode(
    x=alt.X('distance_miles:Q', title='Distance (Miles)'),
    y=alt.Y('duration_minutes:Q', title='Duration (Minutes)'),
    color=alt.condition(
        cell_select,
        alt.Color('mode_of_transportation:N', title='Mode'),
        alt.value('lightgray')
    ),
    opacity=alt.condition(cell_select, alt.value(0.9), alt.value(0.3)),
    tooltip=['day_of_week', 'mode_of_transportation', 'weather',
             'duration_minutes', 'distance_miles']
).properties(
    title="Distance vs Commute Time by Mode",
    width=400,
    height=350
)

dashboard = (heatmap | scatter).resolve_scale(color='independent')

dashboard.save('task5_dashboard.html')
print("Saved dashboard to task5_dashboard.html")