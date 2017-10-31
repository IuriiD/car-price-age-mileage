# for given makes get models lists from auto.ria.ua and store each list in a separate txt file

import requests

# in future this dictionary may be fetched from a file (makes.txt)
makes_needed = {'Alfa Romeo': 3, 'Bentley': 8, 'BMW': 9, 'Chevrolet': 13, 'Chrysler': 14, 'Citroen': 15, 'Daewoo': 18, 'Mazda': 47, 'Mercedes-Benz': 48, 'Mitsubishi': 52, 'Opel': 56, 'Skoda': 70}

# function takes a filename, gets from that file a string and parses it into a dictionary with keys (make or model names) and values (integers for corresponding makes/models)
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

# get model list for given make (for eg., Citroen (15) and Opel (56)
# parse it and store to files
for key, value in makes_needed.items():
    r = requests.get('http://api.auto.ria.com/categories/1/marks/'+str(value)+'/models?api_key=xmDSGYkL0FDq7VTLAMDfOW2AXD5kKZYIlWaUtGqr')
    handparser(r.text,key+'.txt')


