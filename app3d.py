import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.plotly as py
import plotly.graph_objs as go
from pymongo import MongoClient

import requests, json
from flask import Flask, render_template, url_for, session, request, redirect, session, flash
from flask_bootstrap import Bootstrap
from cpam_functions import simplifydic, get_price_age_mileage
from keys import api_key, useradmin, sessionskey
import string, random

ads_analysed = 20 # quantity of adverticements requested for analysis


app = dash.Dash()

client = MongoClient()
db = client.makemodels
makesmodelscll = db.makesmodelscll  # collection for 'make name/make ID/model name/model ID's (~3.7k docs)
mks = db.makes  # collection for 'make name/make ID's (~265 docs)

# Prepare a list of makes
makes = []
for doc in mks.find():
    makes.append(doc['make'])
makes = sorted(makes)

# Prepare a list of urls ('/make_name/model_name')
makemodellist = []
for make in makes:
    models4make = []
    for doc in makesmodelscll.find({'make': make}):
        models4make.append(doc['make'] + '/' + doc['model'])
    # Make a list in format [[make_name1, [model_name1, model_name2, model_name3, ...]], [make_name2, [model_name1, model_name2, model_name3, ...]], ...]
    makemodellist.append([make, sorted(models4make)])
    makemodellist = sorted(makemodellist)
#print(makemodellist)

outputlist = []
for makemodel in makemodellist:
    for model in makemodel[1]:
        outputlist.append({'label': model.replace('/',' '), 'value': model})

app.layout = html.Div([
    html.Label('Please select a car model'),
    dcc.Dropdown(id='my-id', options=outputlist, value='Choose a model'),
    #html.Div(id='my-div'),
    dcc.Graph(id='graph3d'),
])

@app.callback(
    dash.dependencies.Output('graph3d', 'figure'),
    [dash.dependencies.Input('my-id', 'value')])
def update_output_div(input_value):
    traces = []
####
    make = input_value[:input_value.find('/')]
    model = input_value[input_value.find('/')+1:]

    client = MongoClient()
    db = client.makemodels
    makesmodelscll = db.makesmodelscll  # collection for 'make name/make ID/model name/model ID's (~3.7k docs)

    # For a given make and model get make_ID and model_ID from DB
    makeID = makesmodelscll.find_one({'make': make})['make_id']
    modelID = makesmodelscll.find_one({'make': make, 'model': model})['model_id']

    # Make requests to auto.ria.ua API and get IDs of adverticements for given model
    r3 = requests.get(
        'https://developers.ria.com/auto/search?api_key=' + api_key + '&category_id=1&marka_id=' + str(
            makeID) + '&model_id=' + str(modelID) + '&countpage=' + str(ads_analysed))
    parsed_IDs = json.loads(r3.text)
    adsIDlist = []
    adsIDstr = parsed_IDs['result']['search_result']['ids']
    for id in adsIDstr:
        adsIDlist.append(int(id))
    # We'll display an alert before charts if there are less than 5 ads on auto.ria.ua for a given model
    toofewads = False
    print('Ads list: ', adsIDlist)
    if len(adsIDlist) < 5:
        toofewads = True

    # Check if any ads for given model exist. If no - abort further steps and render charts.html with
    # notice "Sorry, but no adverticements were found for this model, can't build charts. Please choose another model"
    if not adsIDlist:
        print('No ads')

    # If we have at least 1 ads for a given model, proceed:
    else:
        # Get price/age/mileage data for each ads
        finaldatajson = []  # list of dictionaries in format [{'ads_id': ads1id, 'price': price1, 'age': age1, 'mileage': mileage1}, {'ads_id': ads2id, 'price': price2, 'age': age2, 'mileage': mileage2}, ...]
        for adsid in adsIDlist:
            r4 = requests.get('https://developers.ria.com/auto/info?api_key=' + api_key + '&auto_id=' + str(adsid))
            parsed_ads = json.loads(r4.text)
            finaldatajson.append(get_price_age_mileage(parsed_ads))

        # So now we have a list of ads requested from auto.ria.ua
        # Let's check if we already have a collection of ads for this model (named 'makeID-modelID')
        collectionname = str(makeID) + '-' + str(modelID)
        if collectionname in db.collection_names():
            # If 'yes', let's retrieve these data from db,
            alreadyindb = []  # list of dictionaries in format [{'ads_id': ads1id, 'price': price1, 'age': age1, 'mileage': mileage1}, {'ads_id': ads2id, 'price': price2, 'age': age2, 'mileage': mileage2}, ...]
            for post in db[collectionname].find():
                alreadyindb.append({'ads_id': post['ads_id'], 'price': post['price'], 'age': post['age'],
                                    'mileage': post['mileage']})
            # we may have 1) new ads that are absent in db, 2) ads that's already in db and 3) ads in db that were absent in our request
            # we shall add to db ads belonging to cat. #1, update if needed, ads cat. #2 and delete ads cat. #3
            # Iterate through our existing data
            for dic in alreadyindb:
                oldadsID = dic['ads_id']

                # Retrieve our new ads with the same ID
                newads = next((item for item in finaldatajson if item["ads_id"] == oldadsID), False)
                # If a document for ads that's already in our db coinsides with a requested ads - update it if needed (price, age, mileage)
                if newads:
                    # Our old ads = 'dic'
                    # Get old price, age, mileage
                    pricewas = dic['price']
                    agewas = dic['age']
                    mileagewas = dic['mileage']
                    # Get new price, age, mileage
                    newprice = newads['price']
                    newage = newads['age']
                    newmileage = newads['mileage']
                    priceflag, ageflag, mileageflag = False, False, False
                    datatoupdate = {}
                    if pricewas != newprice:
                        datatoupdate['price'] = newprice
                        priceflag = True
                    if agewas != newage:
                        datatoupdate['age'] = newage
                        ageflag = True
                    if mileagewas != newmileage:
                        datatoupdate['mileage'] = newmileage
                        mileageflag = True
                    if priceflag or ageflag or mileageflag:
                        db[collectionname].update_one({'ads_id': oldadsID}, {
                            '$set': datatoupdate})  # Go update the document in db with new values
                # If we have a document in our collection which is absent in our new request - delete it from collection
                else:
                    db[collectionname].delete_one({'ads_id': oldadsID})
            # Also we have to iterate through our new ads to find such ones that were'nt added to our collection yet and add them
            for dic in finaldatajson:
                newadsID = dic['ads_id']
                if not next((item for item in alreadyindb if item["ads_id"] == newadsID), False):
                    db[collectionname].insert_one(dic)

        # If we don't have a collection of ads for this model, create it and populate with ads
        else:
            result = db[collectionname].insert_many(finaldatajson)

        # Let's draw charts. Retrieve price-age-mileage data from DB
        print('Retrieve price-age-mileage data from DB')
        datafromdb = []
        for post in db[collectionname].find():
            datafromdb.append([post['ads_id'], post['price'], post['age'], post['mileage']])

        # Draw charts using plot.ly
        price_age_chart_name = 'Price($) vs. Age (years): ' + make + '-' + model
        price_mileage_chart_name = 'Price($) vs. Mileage (x1000km): ' + make + '-' + model
        mileage_age_chart_name = 'Age (years) vs. Mileage (x1000km): ' + make + '-' + model

        ages, prices, mileages = [], [], []
        for every_ads in datafromdb:
            ages.append(every_ads[2])
            prices.append(every_ads[1])
            mileages.append(every_ads[3])

    print('Make: ', make)
    print('Model: ', model)
    print('Ages: ', ages)
    print('Prices: ', prices)
    print('Mileages: ', mileages)

    # So now we have all the data, let's feed it to plot.ly charts
    trace = go.Scatter3d(
        x=ages,
        y=prices,
        z=mileages,
        mode='markers',
        marker=dict(
            size=12,
            line=dict(
                color='rgba(217, 217, 217, 0.14)',
                width=0.5
            ),
            opacity=0.9
        )
    )

    data = [trace]
    layout = go.Layout(margin=dict(l=0, r=0, b=0, t=0), xaxis={'title': 'Age (years)'}, yaxis={'title': 'Price ($)'})
    figure = dict(data=data, layout=layout)
    return figure


app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"})

if __name__ == '__main__':
    app.run_server(port=5000,debug=True,host='0.0.0.0')