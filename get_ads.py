import requests

# get ads for Citroen(15) Berlingo(126); get 100 ads and write them to file

# function that gets ads IDs from the string fetched by API request
def parse_IDs(inputstr):
    before_ids = inputstr.index('"ids":[')
    after_ids = inputstr.index('],"count"')

    mylist = inputstr[before_ids + 7:after_ids].split('","')
    mylist[0] = mylist[0][1:]
    mylist[len(mylist) - 1] = mylist[len(mylist) - 1][:-1]

    finallist = []
    for x in range(len(mylist)):
        finallist.append(int(mylist[x]))
    return finallist

# 1st request to check how many ads we have: we need 100 or the actual quantity whatever is bigger
r = requests.get('https://developers.ria.com/auto/search?api_key=xmDSGYkL0FDq7VTLAMDfOW2AXD5kKZYIlWaUtGqr&category_id=1&marka_id=15&model_id=126')
before_count = r.text.index('count')
after_count = r.text.index('last_id')
count = int(r.text[before_count+7:after_count-2])
tens = count / 10
if tens%1!=0:
    tens = tens - tens%1 + 1

take10pages = 10
if tens>1:
    if take10pages>tens:
        take10pages = int(tens)

ID_list = []
for x in range(take10pages):
    r = requests.get('https://developers.ria.com/auto/search?api_key=xmDSGYkL0FDq7VTLAMDfOW2AXD5kKZYIlWaUtGqr&category_id=1&marka_id=15&model_id=126&page='+str(x)+'')
    for item in parse_IDs(r.text):
        ID_list.append(item)

with open('citroen_berlingo_ads_id.txt', 'a') as fh:
    for item in ID_list:
        fh.write(str(item)+'\n')

print(ID_list)
