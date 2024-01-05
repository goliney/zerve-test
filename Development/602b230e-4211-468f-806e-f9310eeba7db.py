fig = px.scatter(
    df.query("year==2007"),
    x="gdp_per_capita",
    y="lifeExp",
    size="population",
    color="continent",
    hover_name="country",
    log_x=True,
    size_max=60,
)
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9966FF"),
    showlegend=False,
    xaxis=dict(
        title="GDP per capita (dollars)", gridcolor="#9966FF", type="log", gridwidth=0.1
    ),
    yaxis=dict(title="Life Expectancy (years)", gridcolor="#9966FF", gridwidth=0.1),
)
