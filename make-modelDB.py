# Script makes requests to auto.ria.ua API and
# Stores to mongo DB in each document the following data: make name, make ID, model name, model ID

import requests, json, pygal
from pymongo import MongoClient
from cpam_functions import simplifydic, get_price_age_mileage
from keys import api_key
ads_analysed = 5 # quantity of adverticements requested for analysis
make_needed = 'Citroen' #'Opel'
model_needed = 'Berlingo пасс.' #'Zafira'
# 0. Create a db with collection, drop collection
client = MongoClient()
db = client.makemodels
cll = db.cll
cll.drop()

# 1. Get a list of makes and corresponding make IDs
r1 = requests.get('https://developers.ria.com/auto/categories/1/marks?api_key=' + api_key)

# 1.1 Parse received json
parsed_makes = json.loads(r1.text)

# 1.2 Simplify received list of dictionaries like [{'name': 'Make1', 'value': MakeID1}, {'name': 'Make2', 'value': MakeID2}, ...]
# to a dictionary like {'Make1': ID1, 'Make2': ID2, ...}
makesdic = simplifydic(parsed_makes)

print('Our makes list:')
print(makesdic)

# 2. Function takes make name and 1) requests a list of models/modelIDs for it, 2) parces it, 3) prepares a list of
# dictionaries ([{'make': 'makename1', 'make_id': 'makename1ID', 'model': 'modelname1', 'model_id': modelname1ID}, {}])
# and stores it to mongoDB
def storemakemodeldata(makename, makeID):
    # 2.1 For given makeID get a list of models
    r2 = requests.get('http://api.auto.ria.com/categories/1/marks/' + str(makeID) + '/models?api_key=' + api_key)

    # 2.1.1 Parse received json
    parsed_models = json.loads(r2.text)

    # 2.1.2 Simplify from [{"name": "Model1", "value": "Model1ID"}, {"name": "Model2", "value": "Model2ID"}, ...]
    # to {'Model1': Model1ID, 'Model2': Model2ID, ...}
    modelsdic = simplifydic(parsed_models)

    print('Moldels list for %s make:' % makename)
    print(modelsdic)
    # in case make has no models (as in case of 'Прицеп', insert {'None': 0} - at least 4 makes
    if not modelsdic:
        modelsdic['None'] = 0

    #2.2 Prepare a list of dictionaries [{'make': 'makename1', 'make_id': 'makename1ID', 'model': 'modelname1', 'model_id': modelname1ID}, {}]
    makeIDmodelID = []
    for key, value in modelsdic.items():
        makeIDmodelID.append({'make': makename, 'make_id': makeID, 'model': key, 'model_id': value})
    print(makeIDmodelID)

    # 2.3 Save data to DB
    result = cll.insert_many(makeIDmodelID)
    print('Data saved successfully!')
    return True


# 3. Iterate throgh makes dictionary, get make name and ID and execute function for storing models for that make to DB
for key, value in makesdic.items():
    makename = key
    makeID = value
    storemakemodeldata(makename, makeID)