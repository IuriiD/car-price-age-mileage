# -*- coding: utf-8 -*-
# Functions used in car-price-age-mileage project
# Iurii Dziuban / iurii.dziuban@gmail.com
# v. 0.2 / 01.11.2017

import datetime

# Simplify received list of dictionaries like [{'name': 'Name1', 'value': Value1}, {'name': 'Name2', 'value': Value2}, ...]
# to a dictionary like {'Make1': ID1, 'Make2': ID2, ...}
def simplifydic(inputlist):
    outputdic = {}
    for everydic in inputlist:
        outputdic[everydic['name']] = everydic['value']
    return(outputdic)

# Function takes parsed json, selects and returns a dictionary {'ads_id': ads1ID, 'price': price1, 'age': age1, 'mileage': milleagekm1}
def get_price_age_mileage(parsedjson):
    now = datetime.datetime.now()
    curr_year = now.year
    adsid = 0
    price = 0
    age = 0
    mileage = 0
    adsid = parsedjson['autoData']['autoId']
    price = parsedjson['USD']
    age = curr_year - parsedjson['autoData']['year']
    defaultmileage = 1 # some ads for unknown reason have no key for mileage in km
    mileage = parsedjson['autoData'].get('raceInt', defaultmileage)
    #mileage = parsedjson['autoData']['raceInt']
    outputdic = {'ads_id': adsid, 'price': price, 'age': age, 'mileage': mileage}
    return outputdic