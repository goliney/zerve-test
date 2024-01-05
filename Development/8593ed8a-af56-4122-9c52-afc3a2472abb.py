fig3 = px.bar(
    ireland_data,
    x="year",
    y="population",
    color="lifeExp",
    labels={"population": "Population of Canada"},
)
fig3.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9966FF"),
)

