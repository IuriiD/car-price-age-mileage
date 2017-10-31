    # we have a list of dictionaries, each of which has 2 pairs of elements - [{'name': 'Name1', 'value': Int1}, {'name': 'Name2', 'value': Int2}, ...]
    # let's reformat it to a dictionary {Name1: Int2, Name2: Int2}

# function takes a filename, gets from that file a string and parses it into a dictionary with keys (make or model names) and values (integers for corresponding makes/models)
def handparser(inputfile, outputfile):
    outputdic = {}

    with open(inputfile, 'r', encoding='utf8') as fh:
        extract = fh.readline()

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

handparser('makes.txt','makes_parsed.txt')