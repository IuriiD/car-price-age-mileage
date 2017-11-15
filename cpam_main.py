import requests, json, pygal
from pymongo import MongoClient
from cpam_functions import simplifydic, get_price_age_mileage
from keys import api_key
ads_analysed = 5 # quantity of adverticements requested for analysis

# TEMPORARY: Here go variables that will be entered by a user via form
make_needed = 'Citroen' #'Opel'
model_needed = 'Berlingo пасс.' #'Zafira'

# 1. Get a list of makes and corresponding make IDs
r1 = requests.get('https://developers.ria.com/auto/categories/1/marks?api_key=' + api_key)

# 1.1 Parse received json
parsed_makes = json.loads(r1.text)

# 1.2 Simplify received list of dictionaries like [{'name': 'Make1', 'value': MakeID1}, {'name': 'Make2', 'value': MakeID2}, ...]
# to a dictionary like {'Make1': ID1, 'Make2': ID2, ...}
makesdic = simplifydic(parsed_makes)

# 2. Find ID for a needed make
for key, value in makesdic.items():
    if key == make_needed:
        makeID = value

# 3. For given makeID get a list of models
r2 = requests.get('http://api.auto.ria.com/categories/1/marks/' + str(makeID) + '/models?api_key=' + api_key)

# 3.1 Parse received json
parsed_models = json.loads(r2.text)

# 3.2 Simplify from [{"name": "Model1", "value": "Model1ID"}, {"name": "Model2", "value": "Model2ID"}, ...]
# to {'Model1': Model1ID, 'Model2': Model2ID, ...}
modelsdic = simplifydic(parsed_models)

# 4. Find ID for a needed model
for key, value in modelsdic.items():
    if key == model_needed:
        modelID = value

# 5. For given model ID get at least ads_analysed (for eg., 50-100) or all existing adverticements' ID
r3 = requests.get('https://developers.ria.com/auto/search?api_key=' + api_key + '&category_id=1&marka_id=' + str(makeID) + '&model_id=' + str(modelID) + '&countpage=' + str(ads_analysed))
parsed_IDs = json.loads(r3.text)
adsIDlist = []
adsIDstr = parsed_IDs['result']['search_result']['ids']
for id in adsIDstr:
    adsIDlist.append(int(id))
print(adsIDlist)

# 6. For each adsID request the adverticement and select ads ID, price($), year and mileage(x1000km)
finaldata = [] # list in format [[adsID1, price$1, year1, mileage1], [adsID2, price$2, year2, mileage2], ...]
for adsid in adsIDlist:
    r4 = requests.get('https://developers.ria.com/auto/info?api_key=' + api_key + '&auto_id=' + str(adsid))
    parsed_ads = json.loads(r4.text)
    finaldata.append(get_price_age_mileage(parsed_ads))


# Originally database was not used and finaldata list was used to build charts
# But let's save data to a MongoDB database, then request it from there and build charts

# 7. Prepare dictionary for saving data to MongoDB
finaldatajson = []
for ads in finaldata:
    finaldatajson.append({'ads_id': ads[0], 'price': ads[1], 'age': ads[2], 'mileage': ads[3]})

print('finaldata',finaldata)
print('finaldatajson',finaldatajson)

# 8. Save data to DB
client = MongoClient()
db = client.autodatabase
posts = db.posts
result = posts.insert_many(finaldatajson)

# 9. Retrieve data from DB and store it to a list of lists [[adsID1, price$1, year1, mileage1], [adsID2, price$2, year2, mileage2], ...]
datafromdb = []
for post in posts.find():
    datafromdb.append([post['ads_id'], post['price'], post['age'], post['mileage']])
print(datafromdb)

# 10. Draw charts using pygal
price_age_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False, title=u'Price($) vs. Age (years): '+make_needed+'-'+model_needed, x_title='Age (years)', y_title='Price ($)',tooltip_border_radius=10, dots_size=5)
price_mileage_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False, title=u'Price($) vs. Mileage (x1000km): '+make_needed+'-'+model_needed, x_title='Mileage (x1000km)', y_title='Price ($)',tooltip_border_radius=10, dots_size=5)
mileage_age_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False, title=u'Age (years) vs. Mileage (x1000km): '+make_needed+'-'+model_needed, x_title='Mileage (x1000km)', y_title='Age (years)',tooltip_border_radius=10, dots_size=5)
for every_ads in datafromdb:
    price_age_XY.add(str(every_ads[0]), [[every_ads[2], every_ads[1]]])
    price_mileage_XY.add(str(every_ads[0]), [[every_ads[3], every_ads[1]]])
    mileage_age_XY.add(str(every_ads[0]), [[every_ads[3], every_ads[2]]])
price_age_XY.render_to_file(make_needed+'-'+model_needed+'-'+'price_age.svg')
price_mileage_XY.render_to_file(make_needed+'-'+model_needed+'-'+'price_mileage.svg')
mileage_age_XY.render_to_file(make_needed+'-'+model_needed+'-'+'age_mileage.svg')
# readjusting git