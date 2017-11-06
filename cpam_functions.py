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

# Function takes parsed json, selects and returns a list [price$, year, mileage]
def get_price_age_mileage(parsedjson):
    #print(parsedjson)
    now = datetime.datetime.now()
    curr_year = now.year
    adsid = 0
    price = 0
    age = 0
    mileage = 0
    adsid = parsedjson['autoData']['autoId']
    price = parsedjson['USD']
    age = curr_year - parsedjson['autoData']['year']
    mileage = parsedjson['autoData']['raceInt']
    outputlist = [adsid, price, age, mileage]
    return outputlist
