from flask import Flask, render_template, url_for
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
import requests, json, pygal
from cpam_functions import simplifydic, get_price_age_mileage
from keys import api_key
ads_analysed = 10 # quantity of adverticements requested for analysis

app = Flask(__name__)
bootstrap = Bootstrap(app)
#
# Flask decorator, index page
@app.route('/')
def index():
    client = MongoClient()
    db = client.makemodels
    cll = db.cll # Collection of documents each containing make_name, make_id, model_name, model_id
    mks = db.makes # Collection of documents with makes names

    # Prepare a list of makes
    makes = []
    for doc in mks.find():
        makes.append(doc['make'])
    makes = sorted(makes)

    # Prepare a list of urls ('/make_name/model_name')
    makemodellist = []
    for make in makes:
        models4make = []
        for doc in cll.find({'make': make}):
            models4make.append('/' + doc['make'] + '/' + doc['model'])
        # Make a list in format [[make_name1, [model_name1, model_name2, model_name3, ...]], [make_name2, [model_name1, model_name2, model_name3, ...]], ...]
        makemodellist.append([make, sorted(models4make)])
        makemodellist = sorted(makemodellist)
    # Render html with our list passed
    return render_template('index.html', makemodellist=makemodellist)

@app.route('/<make>/<model>')
def getcharts(make, model):
    client = MongoClient()
    db = client.makemodels
    cll = db.cll # Collection of documents each containing make_name, make_id, model_name, model_id
    mks = db.makes # Collection of documents with makes names

    # cpam_main.py >> #5
    # For given make and model get make_ID and model_ID from DB
    makeID = cll.find_one({'make': make})['make_id']
    modelID = cll.find_one({'make': make, 'model': model})['model_id']

    # Make requests to auto.ria.ua API and get IDs of adverticements for given model
    r3 = requests.get('https://developers.ria.com/auto/search?api_key=' + api_key + '&category_id=1&marka_id=' + str(
        makeID) + '&model_id=' + str(modelID) + '&countpage=' + str(ads_analysed))
    parsed_IDs = json.loads(r3.text)
    adsIDlist = []
    adsIDstr = parsed_IDs['result']['search_result']['ids']
    for id in adsIDstr:
        adsIDlist.append(int(id))

    # Get price/age/mileage data for each ads
    finaldata = []  # list in format [[adsID1, price$1, year1, mileage1], [adsID2, price$2, year2, mileage2], ...]
    for adsid in adsIDlist:
        r4 = requests.get('https://developers.ria.com/auto/info?api_key=' + api_key + '&auto_id=' + str(adsid))
        parsed_ads = json.loads(r4.text)
        finaldata.append(get_price_age_mileage(parsed_ads))

    # Save price-age-mileage data to DB
    finaldatajson = []
    for ads in finaldata:
        finaldatajson.append({'ads_id': ads[0], 'price': ads[1], 'age': ads[2], 'mileage': ads[3]})
    mymodel = db.mymodel  # Collection of documents with price/age/mileage data for a given model
    mymodel.drop()
    result = mymodel.insert_many(finaldatajson)

    # Retrieve price-age-mileage data from DB
    datafromdb = []
    for post in mymodel.find():
        datafromdb.append([post['ads_id'], post['price'], post['age'], post['mileage']])

    # Draw charts using pygal lib
    price_age_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False,
                            title=u'Price($) vs. Age (years): ' + make + '-' + model,
                            x_title='Age (years)', y_title='Price ($)', tooltip_border_radius=10, dots_size=5, width=600, height=600)
    price_mileage_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False,
                                title=u'Price($) vs. Mileage (x1000km): ' + make + '-' + model,
                                x_title='Mileage (x1000km)', y_title='Price ($)', tooltip_border_radius=10, dots_size=5, width=600, height=600)
    mileage_age_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False,
                              title=u'Age (years) vs. Mileage (x1000km): ' + make + '-' + model,
                              x_title='Mileage (x1000km)', y_title='Age (years)', tooltip_border_radius=10, dots_size=5, width=600, height=600)
    for every_ads in datafromdb:
        price_age_XY.add(str(every_ads[0]), [[every_ads[2], every_ads[1]]])
        price_mileage_XY.add(str(every_ads[0]), [[every_ads[3], every_ads[1]]])
        mileage_age_XY.add(str(every_ads[0]), [[every_ads[3], every_ads[2]]])
    ch_pa = 'static/' + make + '-' + model + '-' + 'price_age.svg' # name of chart price-age
    ch_pm = 'static/' + make + '-' + model + '-' + 'price_mileage.svg' # name of chart price-mileage
    ch_ma = 'static/' + make + '-' + model + '-' + 'age_mileage.svg'# name of chart mileage-age
    price_age_XY.render_to_file(ch_pa)
    price_mileage_XY.render_to_file(ch_pm)
    mileage_age_XY.render_to_file(ch_ma)#
    ch_pa = '/' + ch_pa
    ch_pm = '/' + ch_pm
    ch_ma = '/' + ch_ma
    # Render page using saved charts (need to decide what to do with them next)
    return render_template('charts.html', make=make, model=model, ch_pa=ch_pa, ch_pm=ch_pm, ch_ma=ch_ma)

# Run Flask server (host='0.0.0.0' - for Vagrant)
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)

