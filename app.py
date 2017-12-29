from flask import Flask, render_template
import json
import plotly

app = Flask(__name__)

@app.route('/')
def index():
    graphs = [
        dict(
            data=[
                dict(
                    x=[1, 2, 3, 4, 5, 10],
                    y=[10, 20, 30, 35, 40, 48],
                    type='scatter',
                    mode='markers',
                    marker={'color': 'red', 'size': "10"}
                ),
            ],
            layout=dict(
                title='Price($) vs. Age (years)',
                xaxis={'title': 'x1'}, yaxis={'title': 'x2'}
            )
        )
    ]

    ids = ['graph-{}'.format(i) for i, _ in enumerate(graphs)]
    graphJSON = json.dumps(graphs, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('plotly.html',
                           ids=ids,
                           graphJSON=graphJSON)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)