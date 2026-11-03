import pandas as pd
import altair as alt

df = pd.read_csv("data/processed/commutes_clean.csv")

days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
modes = sorted(df['mode_of_transportation'].dropna().unique().tolist())

mode_color = alt.Color('mode_of_transportation:N', title='Mode',
                       scale=alt.Scale(domain=modes))

#STATIC: small multiples, one panel per mode, shared y-axis 
static = alt.Chart(df).mark_bar().encode(
    x=alt.X('day_of_week:N', sort=days_order, title=None,
            axis=alt.Axis(labelAngle=-45)),
    y=alt.Y('mean(duration_minutes):Q', title='Average Commute Time (Minutes)'),
    color=alt.Color('mode_of_transportation:N', legend=None,
                    scale=alt.Scale(domain=modes)),
    column=alt.Column('mode_of_transportation:N', title=None)
).properties(
    title='Static: Average Commute Time by Day, per Mode',
    width=110, height=300
)

#INTERACTIVE: grouped bars, legend click filters modes
mode_select = alt.selection_point(fields=['mode_of_transportation'], bind='legend')

interactive = alt.Chart(df).mark_bar().encode(
    x=alt.X('day_of_week:N', sort=days_order, title='Day of Week'),
    xOffset=alt.XOffset('mode_of_transportation:N'),
    y=alt.Y('mean(duration_minutes):Q', title='Average Commute Time (Minutes)'),
    color=mode_color
).add_params(mode_select).transform_filter(mode_select).properties(
    title='Interactive: click legend to filter by mode (shift-click for several)',
    width=400, height=300
)

static.save('static_bar.html')
interactive.save('interactive_bar.html')