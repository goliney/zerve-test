gapminder2007 = df.query("year == 2007")
fig4 = px.scatter(gapminder2007, x="gdp_per_capita", y="lifeExp")
fig4.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9966FF"),
    xaxis=dict(title="GDP per capita (dollars)", gridcolor="#aa8fdf", gridwidth=0.1),
    yaxis=dict(title="Life Expectancy (years)", gridcolor="#aa8fdf", gridwidth=0.1),
)
