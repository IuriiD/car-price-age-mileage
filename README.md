# car-price-age-mileage / Correlating car's price, age and mileage - data from auto.ria.ua
This is my 1st real project while learning to code.

Task: to create a web service where a user can enter a car make/model and get 3 charts (scatter diagrams) showing correlation of car's
a) age/price, b) mileage/price and c) age/mileage.

Data will be taken from auto.ria.ua (the biggest Ukrainian automotive advertisement board where, as they claim, '1400 cars are sold daily')
using their API (https://github.com/ria-com/auto-ria-rest-api) (alternatively - from eBay Motors using eBay Finding API, 
https://developer.ebay.com/Devzone/finding/Concepts/FindingAPIGuide.html)

Topics to learn:
- Creating Vagrant boxes in Virtualbox (working on a PC with Win7 64bit)
- Setting up virtualenv, Python3 and libraries (requests, json, flask, pymongo, pygal), MongoDB in Vagrant
- Git
