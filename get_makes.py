# get makes list from auto.ria.ua via API and using requests, parse it and save in txt file

import requests

# function takes a string (= request via auto.ria.ua API), gets from that file a string and parses it into a dictionary with keys (make or model names) and values (integers for corresponding makes/models)
def handparser(inputstr, outputfile):
    outputdic = {}

    extract = inputstr

    splitlist = extract.split('{"name":"')
    splitlist = splitlist[1:]

    nextlist = []
    for item in splitlist:
        templist = item.split('","value":')
        for x in templist:
            nextlist.append(x)
        templist = []

    finallist = []
    for y in nextlist:
        if '},' in y:
            finallist.append(y[:-2])
        else:
            finallist.append(y)

    finallist[len(finallist)-1] = finallist[len(finallist)-1][:-2]

    name = ''
    id = 0

    for m in range(len(finallist)):
        if m%2==0:
            name = finallist[m]
        else:
            id = int(finallist[m])
        if name != '' and id != 0:
            outputdic[name] = id
            name = ''
            id = 0

    #print(extract)
    #print(finallist)
    print(outputdic)

    with open(outputfile, 'a') as f2wh:
        for key, value in outputdic.items():
            f2wh.write(key+': '+str(value)+'\n')


r = requests.get('https://developers.ria.com/auto/categories/1/marks?api_key=xmDSGYkL0FDq7VTLAMDfOW2AXD5kKZYIlWaUtGqr')
handparser(r.text,'makes.txt')

