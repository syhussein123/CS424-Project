import pandas as pd
import altair as alt

df = pd.read_csv("data/processed/commutes_clean.csv")


plotly_palette = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
                  '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
modes = df['mode_of_transportation'].dropna().unique().tolist()
mode_scale = alt.Scale(domain=modes, range=plotly_palette[:len(modes)])

brush = alt.selection_interval(encodings=['x'])  # drag across a distance range
mode_select = alt.selection_point(fields=['mode_of_transportation'], bind='legend')

#Main scatter: same encoding as the static version 
scatter = alt.Chart(df).mark_circle(size=64).encode(
    x=alt.X('distance_miles:Q', title='Distance (Miles)'),
    y=alt.Y('duration_minutes:Q', title='Commute Time (Minutes)'),
    color=alt.Color('mode_of_transportation:N', title='Transport Mode', scale=mode_scale),
    opacity=alt.condition(brush & mode_select, alt.value(0.8), alt.value(0.1)),
    tooltip=[
        alt.Tooltip('day_of_week:N', title='Day'),
        alt.Tooltip('weather:N', title='Weather'),
        alt.Tooltip('location_clean:N', title='Location'),
        alt.Tooltip('mode_of_transportation:N', title='Mode'),
        alt.Tooltip('distance_miles:Q', title='Distance (mi)'),
        alt.Tooltip('duration_minutes:Q', title='Duration (min)')
    ]
).add_params(brush, mode_select).properties(
    title='Drag across a distance range; click legend to isolate a mode',
    width=420, height=350
)

#Linked chart: mean and spread per mode for the brushed trips
summary_base = alt.Chart(df).transform_filter(brush).transform_filter(mode_select)

bars = summary_base.mark_bar(opacity=0.85).encode(
    y=alt.Y('mode_of_transportation:N', title=None, scale=alt.Scale(domain=modes)),
    x=alt.X('mean(duration_minutes):Q', title='Average Commute Time (Minutes), error bar = ±1 SD'),
    color=alt.Color('mode_of_transportation:N', legend=None, scale=mode_scale),
    tooltip=[
        alt.Tooltip('mode_of_transportation:N', title='Mode'),
        alt.Tooltip('mean(duration_minutes):Q', title='Mean (min)', format='.1f'),
        alt.Tooltip('stdev(duration_minutes):Q', title='SD (min)', format='.1f'),
        alt.Tooltip('count():Q', title='Trips')
    ]
)

spread = summary_base.mark_errorbar(extent='stdev', color='black').encode(
    y=alt.Y('mode_of_transportation:N', scale=alt.Scale(domain=modes)),
    x=alt.X('duration_minutes:Q')
)

summary = (bars + spread).properties(
    title='Selected trips: average and spread by mode',
    width=300, height=350
)

interactive = (scatter | summary).resolve_scale(color='independent')
interactive.save('interactive.html')


#fig_scatter.write_html('static.html')
print("Saved interactive.html")