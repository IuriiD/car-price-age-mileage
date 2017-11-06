import requests
import json
import pygal
from cpam_functions import simplifydic, get_price_age_mileage
api_key = 'xmDSGYkL0FDq7VTLAMDfOW2AXD5kKZYIlWaUtGqr'
ads_analysed = 50 # quantity of adverticements requested for analysis

# TEMPORARY: Here go variables that will be entered by a user via form
make_needed = 'Citroen' # 'Opel'
model_needed = 'Berlingo пасс.' # 'Zafira'

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

# 5. For given model ID get at least X (for eg., 50-100) or all existing adverticements' ID
r3 = requests.get('https://developers.ria.com/auto/search?api_key=' + api_key + '&category_id=1&marka_id=' + str(makeID) + '&model_id=' + str(modelID) + '&countpage=' + str(ads_analysed))
parsed_IDs = json.loads(r3.text)
adsIDlist = []
adsIDstr = parsed_IDs['result']['search_result']['ids']
for id in adsIDstr:
    adsIDlist.append(int(id))
print(adsIDlist)

# 6. For each adsID request the adverticement and select price($), year and mileage(x1000km)
finaldata = [] # list in format [[adsID1, price$1, year1, mileage1], [adsID2, price$2, year2, mileage2], ...]
for adsid in adsIDlist:
    r4 = requests.get('https://developers.ria.com/auto/info?api_key=' + api_key + '&auto_id=' + str(adsid))
    parsed_ads = json.loads(r4.text)
    finaldata.append(get_price_age_mileage(parsed_ads))

# 7. Draw charts
# 7.1 Prepare datasets (lists of tuples - [(price1, age1), (price2, age2), ...]) for scatter charts
price_age_data = []
price_mileage_data = []
age_mileage_data = []
for innerdic in finaldata:
    price_age_data.append((innerdic[1], innerdic[0]))
    price_mileage_data.append((innerdic[2], innerdic[0]))
    age_mileage_data.append((innerdic[2], innerdic[1]))
print(price_age_data)
print(price_mileage_data)
print(age_mileage_data)

# 7.2 Draw charts using pygal
# Age-Price
price_age_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False, title=u'Price($) vs. Age (years): '+make_needed+'-'+model_needed, x_title='Age (years)', y_title='Price ($)',tooltip_border_radius=10, dots_size=5)
price_age_XY.add('', price_age_data)
price_age_XY.render_to_file(make_needed+'-'+model_needed+'-'+'price_age.svg')

# Mileage-Price
price_mileage_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False, title=u'Price($) vs. Mileage (x1000km): '+make_needed+'-'+model_needed, x_title='Mileage (x1000km)', y_title='Price ($)',tooltip_border_radius=10, dots_size=5)
price_mileage_XY.add('', price_mileage_data)
price_mileage_XY.render_to_file(make_needed+'-'+model_needed+'-'+'price_mileage.svg')

# Age-Mileage
mileage_age_XY = pygal.XY(stroke=False, show_legend=False, human_readable=True, fill=False, title=u'Age (years) vs. Mileage (x1000km): '+make_needed+'-'+model_needed, x_title='Mileage (x1000km)', y_title='Age (years)',tooltip_border_radius=10, dots_size=5)
mileage_age_XY.add('', age_mileage_data)
mileage_age_XY.render_to_file(make_needed+'-'+model_needed+'-'+'age_mileage.svg')