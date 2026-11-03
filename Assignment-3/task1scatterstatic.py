import pandas as pd
import plotly.express as px

df = pd.read_csv("data/processed/commutes_clean.csv")

modes = df['mode_of_transportation'].dropna().unique().tolist()
palette = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A',
           '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52']
color_map = {m: palette[i] for i, m in enumerate(modes)}

fig_static = px.scatter(
    df,
    x="distance_miles",
    y="duration_minutes",
    color="mode_of_transportation",
    facet_col="mode_of_transportation",
    facet_col_wrap=3,
    category_orders={"mode_of_transportation": modes},
    color_discrete_map=color_map,
    title="Distance vs Commute Time, One Panel per Transport Mode",
    labels={
        "distance_miles": "Distance (Miles)",
        "duration_minutes": "Commute Time (Minutes)",
        "mode_of_transportation": "Transport Mode",
    },
    height=650, width=1050,
)

fig_static.update_traces(marker=dict(size=8, opacity=0.7))
fig_static.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
fig_static.update_layout(showlegend=False)


fig_static.update_xaxes(
    range=[0, df['distance_miles'].max() + 2],
    dtick=5, showgrid=True, gridcolor="lightgray", griddash="dot",
)
fig_static.update_yaxes(range=[0, df['duration_minutes'].max() + 10])


fig_static.write_html('static.html', config={'staticPlot': True})
fig_static.show(config={'staticPlot': True})