import plotly.plotly as py
import plotly.graph_objs as go

trace = go.Scatter(
    x=[1, 2, 3, 4, 5, 10],
    y=[10, 20, 30, 35, 40, 48],
    mode='markers'
)
data = [trace]

# Plot and embed in ipython notebook!
py.iplot(data, filename='basic-scatter')