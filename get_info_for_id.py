import requests
import datetime

# current year for age calculation
now = datetime.datetime.now()
curr_year = now.year

# get info for given ads ID, parse it to get price$, age and mileage
# def find_price_age_mileage(car_ads_id):
r = requests.get('https://developers.ria.com/auto/info?api_key=xmDSGYkL0FDq7VTLAMDfOW2AXD5kKZYIlWaUtGqr&auto_id=20704748')
mystr = r.text
print(mystr)

# get price
price = 0
before_price = mystr.index('USD')+5
after_price = mystr.index('UAH')-2
price = int(mystr[before_price:after_price])

# get age
age = 0
before_age = mystr.index('year')+6
after_age = mystr.index('autoId')-2
age = curr_year - int(mystr[before_age:after_age])

# get mileage
mileage = 0
before_mileage = mystr.index('raceInt')+9
after_mileage = mystr.index('fuelName')-2
mileage = int(mystr[before_mileage:after_mileage])
outputlist = []
outputlist = [20704748, price, age, mileage]
print(outputlist)
#return outputlist

#id_list = [20704748, 20674162]
    #, 20716366, 20641159, 20625199]

#find_price_age_mileage('20704748')

