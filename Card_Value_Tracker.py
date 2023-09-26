import requests
import os
import json
        

def verifyFiles():
    #Ensure existence of directory and file
    userName = os.getlogin()
    hostDir = "C:\\Users\\"+userName+"\\Documents\\CardValueTracker"

    #Create dir
    if(not os.path.isdir(hostDir)):
        try:
            os.mkdir(hostDir)
            print(">>Successfully Created Directory!")
            print(">>@ \"%s\"\n" % hostDir)
        except:
            print(">>Could Not Create Directory.")
            input()
            exit()
            
    #Create file
    hostDir = hostDir + "\\cards_list.txt"
    
    if(not os.path.isfile(hostDir)):
        #Attempt to create file
        f = open(hostDir, 'x')

        if(not os.path.isfile(hostDir)):
            print(">>Could Not Create File.")
            input()
            exit()
        else:
            f.close()
            print(">>Successfully Created File!")
            print(">>@ \"%s\"\n" % hostDir)

    return hostDir

def readDataBase(hostDir):
    #Retrieve file contents
    with open(hostDir, 'r') as fr:
        #Retrieve file contents
        fr.seek(0)
        cardsArr = fr.read().split(',')
        #Prune away eroneous element
        cardsArr.pop()
        
    if len(cardsArr) == 0:
        return {}

    cardsDict = {}

    #Populate dictionary
    for entry in cardsArr:
        split = entry.split('?')
        pair = split[1].split(':')
        #{"cardID": (printType, quantity)}
        cardsDict[int(split[0])] = [pair[0], int(pair[1])]

    return cardsDict

def updateDataBase(hostDir, newContent):
    #Update database
    with open(hostDir, 'w+') as fw:
        #Update database
        for card in newContent.items():
            entry = "%s?%s:%s," % (card[0], card[1][0], card[1][1])
            fw.write(entry)

def calculateValues(hostDir):
    print()
    
    #Retrieve card IDs
    cardsDict = readDataBase(hostDir)
    #Short circuit if database empty
    if(len(cardsDict) == 0):
        print(">>Empty Database.\n")
        main()
        return

    i = 0
    cards = {}

    print(">>Retrieving Values...")
    
    #Load cards in Dict
    for card in cardsDict.items():

        #Make requests
        response = requests.get("https://mp-search-api.tcgplayer.com/v1/product/%s/details" % card[0])
        data = response.json()
        name = data.get("productName")
        
        response = requests.get("https://mpapi.tcgplayer.com/v2/product/%s/pricepoints?mpfev=1814" % card[0])
        data = response.json()
        
        #Seek out card type
        i = 0
        while(data[i].get("printingType").lower() != card[1][0]):
            i += 1

        #-----Load new card in
        #CREATE KEY
        #Card_Type print Card_Name => Card_Value
        s1 = card[1][0].capitalize().ljust(7)
        #Finalize key
        key = "(%s) %s print %s" % (card[1][1],s1, name)
        
        if(data[i].get("marketPrice") == None):
            #Put in 0 if value null
            cards[key] = [0, 0]
        else:
            #Store new pair
            cards[key] = [float(data[i].get("marketPrice")), card[1][1]]

    #Sort by card value in reverse order
    cards = dict(sorted(cards.items(), key=lambda x: x[1][0])[::-1])

    #-------PRINT OUT CARDS----------
    print("\n--------------------")
    #Print Total Cost
    total = 0
    for price in cards.values():
        #Card cost x Quantity
        total += price[0] * price[1]
    print("\nTotal Cost: $%0.2f\n" % total)

    #Find longest string for formatting
    padLen = 0
    for key in cards.keys():
        if( len(key) >= padLen):
            padLen = len(key)
    padLen += 2
    
    #Print high to low by price
    print("High to low by cost =>\n")
    for key, value in cards.items():
        #Format key
        key = "%s:" % key
        #Format value
        value = "$%0.2f" % value[0]
        #Print key and value
        print("%s%s" % (key.ljust(padLen), value))

    #Print tail
    print("--------------------")
    input()

def cardEntry(hostDir):
    while(True):
            #Get next card
            newCard = input("\nEnter card id or url. (-1) to go back.\n")

            #Parse input
            try:
                #If int, it's an id
                newCard = int(newCard)

                #Check if going back to menu
                if(newCard == -1):
                    main()
                    break
            except:
                #Possibly a Link
                #Check if tcgplayer link
                if ("tcgplayer.com" not in newCard):
                    print(">>Invalid Input.\n")
                    continue

                #Sanitize input and extract card id
                #Split by /
                arr = newCard.split('/')
                #Strip https:
                if(arr[0] == "https:"):
                    arr.pop(0)
                if(arr[0] == ''):
                    arr.pop(0)
                #tcg.com/product/id"
                try:
                    newCard = int(arr[2])
                except:
                    print(">>Invalid Input.\n")
                    continue
                
            #Verify id exists
            url = "https://mp-search-api.tcgplayer.com/v1/product/"+str(newCard)+"/details"
            response = requests.get(url)

            #Retreive price points
            if(response.status_code != 200):
                print(">>Invalid ID.\n")
            else:
                #Validate Card type
                url = "https://mpapi.tcgplayer.com/v2/product/"+str(newCard)+"/pricepoints?mpfev=1814"
                response = requests.get(url)
                data = response.json()

                #Check if holo or normal card
                cardTypes = []
                
                for i in range(len(data)):
                    #Retrieve print types
                    cardTypes.append(data[i].get("printingType").lower())

                print("Enter Card Type: ", end='')
                print(cardTypes)
                print()

                #Get input, and verify existence
                cardType = input()
                
                while(not(cardType.lower() in cardTypes)):
                    print(">>Invalid Print Type.\n")
                    print("Enter Card Type: ", end='')
                    print(cardTypes)

                    cardType = input()

            #Retrieve database
            cardsDict = readDataBase(hostDir)

            #Check if in database
            if (newCard in cardsDict):
                #Update quantity of card
                oldQuantity = cardsDict.get(newCard)[1]
                cardsDict.get(newCard)[1] = oldQuantity + 1
            else:
                #Enter new card
                cardsDict[newCard] = [cardType, 1]
            
            updateDataBase(hostDir, cardsDict)
            print(">>Card Successfully Entered.\n")
            
def removeCard(hostDir):
    cardToRemId = -1
    cardsDict = readDataBase(hostDir)

    while(True):
        #Short circuit if database empty
        if(len(cardsDict) == 0):
            print(">>Empty Database.\n")
            main()
            return
            
        cardToRemId = input("\n>>Enter card id or URL to remove. (-1) to return to menu.\n")
            
        #Parse input
        try:
            #If int, it's an id
            cardToRemId = int(cardToRemId)
            #Check if -1
            if(cardToRemId <= 0):
                main()
                break
                
        except:
            #Possibly a Link
            if ("tcgplayer.com" not in str(cardToRemId)):
                print(">>Invalid Input.\n")
                continue
            #Sanitize input and extract card id
            #Split by /
            arr = cardToRemId.split('/')
            #Strip https:
            if(arr[0] == "https:"):
                arr.pop(0)
            if(arr[0] == ''):
                arr.pop(0)
            #tcg.com/product/id"
            try:
                cardToRemId = int(arr[2])
            except:
                print(">>Invalid Input.\n")
                continue
        
        break
    
    if cardToRemId in cardsDict.keys():
        #Confirm deletion with user
        #Grab name
        response = requests.get("https://mp-search-api.tcgplayer.com/v1/product/%s/details" % cardToRemId)
        name = response.json().get("productName")
        #Prompt user
        confirmation = input("Remove \"%s\"? \"Yes\" or \"No\":\n" % name)
        #Initiate deletion
        if(confirmation.lower() == "yes"):
            #Update quantity if q > 1
            if(cardsDict[cardToRemId][1] != 1):
                quantity = cardsDict[cardToRemId][1]
                cardsDict[cardToRemId][1] = quantity - 1
            else:
                cardsDict.pop(cardToRemId)
            
            with open(hostDir, 'w+') as fw:
                updateDataBase(hostDir, cardsDict)

            print(">>Card Successfully removed.\n")
        else:
            print(">>Canceling deletion.\n")
    else:
        print(">>Card not in database.\n")
        
    #Go back to menu
    main()


def main():
    #Verify data file exists, and grab path
    hostDir = verifyFiles()

    #Recieve command
    command = int(input("Please choose an action:\n(1) Enter new cards\n(2) Calculate Values\n(3) Remove Card\n"))

    #Check input
    while(command <= 0 or command > 3):
        print(">>Invalid Input, Try Again.\n")
        command = int(input("Please choose an action:\n(1) Enter new cards\n(2) Calculate Values\n(3) Remove Card\n"))
        
    #Exeggute command
    if(command == 1):
        cardEntry(hostDir)
    elif(command == 2):
        calculateValues(hostDir)
    else:
        removeCard(hostDir)
    
main()
