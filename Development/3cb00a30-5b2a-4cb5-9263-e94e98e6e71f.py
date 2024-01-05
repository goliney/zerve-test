fig5 = px.choropleth(
    df,
    locations="iso_alpha",
    color="lifeExp",
    hover_name="country",
    animation_frame="year",
    color_continuous_scale=px.colors.sequential.Plasma,
    projection="natural earth",
)
fig5.update_layout(
    title_text="Life Expectancy Over Time",
    title_x=0.5,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    geo_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9966FF"),
)
