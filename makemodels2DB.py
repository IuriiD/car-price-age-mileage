# Script makes requests to auto.ria.ua API and stores the following data to 2 mongoDB collections in  'makesmodels'
# mongodb: a) collection 'makes' - 'make name/make ID's; and b) collection 'makesmodelscll' - 'make name/make ID/model name/
# model ID's. Then it checks for makes with 0 models - such makes are not stored to either collection (as for Nov 2017 there
# were 4 such makes: 'Прицеп', 'Peterbilt', 'Peerless', 'Dfcz' - they either have 0 ads on auto.ria.ua or are not cars
# in case of 'Прицеп')
# iurii.dziuban@gmail.com / 22.11.2017

import requests, json
from pymongo import MongoClient
from cpam_functions import simplifydic, get_price_age_mileage
from keys import api_key

# 0. Create a mongodb, collections, drop collections
client = MongoClient()
db = client.makemodels
makes = db.makes # collection for 'make name/make ID's (~265 docs)
makesmodelscll = db.makesmodelscll # collection for 'make name/make ID/model name/model ID's (~3.7k docs)
makes.drop()
makesmodelscll.drop()

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

    # in case make has no models (as in case of 'Прицеп', 'Peterbilt', 'Peerless', 'Dfcz' - Nov 2017),
    # do not store data for this make to 'makesmodelscll' and  'makes' collections (return False)
    if not modelsdic:
        print('%s won\'t be saved to makes and models collections' % makename)
        return False

    #2.2 Prepare a list of dictionaries [{'make': 'makename1', 'make_id': 'makename1ID', 'model': 'modelname1', 'model_id': modelname1ID}, {}]
    makeIDmodelID = []
    for key, value in modelsdic.items():
        makeIDmodelID.append({'make': makename, 'make_id': makeID, 'model': key, 'model_id': value})
    print(makeIDmodelID)

    # 2.3 Save data to DB
    result = makesmodelscll.insert_many(makeIDmodelID)
    print('Data saved successfully!')
    return True


# 3. Iterate throgh 'makes' collection, get make name and ID and execute storemakemodeldata() function for storing models for that make to DB
# Also store makes list in a separate collection
makes2delete = []
for key, value in makesdic.items():
    makename = key
    makeID = value
    if not storemakemodeldata(makename, makeID):
        makes2delete.append(makename)
print('We will not store the following makes: ', makes2delete)

for item in makes2delete:
    del makesdic[item]
print(makesdic)

makes2save = []
for key, value in makesdic.items():
    makes2save.append({'make': key, 'make_ID': value})
result = makes.insert_many(makes2save)