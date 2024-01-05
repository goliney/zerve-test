fig2 = px.bar(canada_data, x="year", y="population")
fig2.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#9966FF"),
)
