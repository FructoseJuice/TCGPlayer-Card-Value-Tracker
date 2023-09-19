import requests
import os
import json
        

def verifyFiles():
    #Ensure existence of directory and file
    userName = os.getlogin()
    hostDir = "C:\\Users\\"+userName+"\\Documents\\PokemonCardValues"

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
    fileName = "cards_list.txt"
    hostDir = hostDir + "\\" + fileName
    
    if(not os.path.isfile(hostDir)):
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

def calculateValues(hostDir):
    print()
    
    #Retrieve card IDs
    with open(hostDir, "r") as fr:
        fr.seek(0)
        fileContent = fr.read().split(',')
        fileContent.pop()

    #Short circuit if database empty
    if(len(fileContent) == 0):
        print(">>Empty Database.\n")
        main()
        return

    cards = {}

    print(">>Retrieving Values...")
    j = 0
    k = 0
    #Load cards in Dict
    for i in range(len(fileContent)):
        #Print loading wheel
        if(i % 2 == 0):
            if(k % 2 == 0):
                print("/", end='')
            else:
                print("\\", end='')
            k += 1
        else:
            if(j % 2 == 0):
                print("|", end='')
            else:
                print("-", end='')
            j += 1
            
        #Load in next card
        card = fileContent[i].split(":")

        #Make requests
        response = requests.get("https://mp-search-api.tcgplayer.com/v1/product/%s/details" % card[1])
        data = response.json()
        name = data.get("productName")
        
        response = requests.get("https://mpapi.tcgplayer.com/v2/product/%s/pricepoints?mpfev=1814" % card[1])
        data = response.json()
        
        #Seek out card type
        i = 0
        while(data[i].get("printingType").lower() != card[0]):
            i += 1

        
        #-----Load new value
        #CREATE KEY
        #Card_Type print Card_Name => Card_Value
        s1 = card[0].capitalize().ljust(7)
        #Finalize key
        key = "%s print %s" % (s1, name)
        
        if(data[i].get("marketPrice") == None):
            #Put in 0 if value null
            cards[key] = 0
        else:
            #Store new pair
            cards[key] = float(data[i].get("marketPrice"))

    #Sort by card value in reverse order
    cards = dict(sorted(cards.items(), key=lambda x: x[1])[::-1])

    #-------PRINT OUT CARDS----------
    print("\n--------------------")
    #Print Total Cost
    print("\nTotal Cost: $%0.2f\n" % float(sum(cards.values())))

    #Find longest string for formatting
    padLen = 0
    for key in cards.keys():
        if( len(key) >= padLen):
            padLen = len(key)
    padLen += 2
    
    #Print high to low by price
    print("High to low by cost =>\n")
    for key, value in cards.items():
        key = "%s:" % key
        value = "$%0.2f" % value
        print(key.ljust(padLen), end='')
        print(value)
    print("--------------------")
    input()


def cardEntry(hostDir):
    while(True):
        with open(hostDir, "a+") as fw:
            #Retrieve file contents
            fw.seek(0)
            fileContent = fw.read().split(',')
            fileContent.pop()
            
            #Get next card
            newCard = input("\nEnter card id or url. (-1) to go back.\n")

            #Go back to start if input -1
            try:
                if(int(newCard) == -1):
                    main()
                    break
            except:
                pass

            #Parse input
            try:
                #If int, it's an id
                newCard = int(newCard)
            except:
                #Possibly a Link
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

            #Validate and store input
            if(response.status_code != 200):
                print(">>Invalid id.\n")
            else:
                #Validate Card type
                url = "https://mpapi.tcgplayer.com/v2/product/"+str(newCard)+"/pricepoints?mpfev=1814"
                response = requests.get(url)
                data = response.json()

                #Check if holo or normal card
                cardTypes = []
                
                for i in range(len(data)):
                    cardTypes.append(data[i].get("printingType").lower())
                print("Enter Card Type: ", end='')
                print(cardTypes)
                print()

                #Get input, and verify existence
                cardType = input()
                
                while(not(cardType.lower() in cardTypes)):
                    print(">>Invalid Input:\n")
                    print("Enter Card Type: ", end='')
                    print(cardTypes)

                    cardTypes = input()
                
                if str(newCard) in fileContent:
                    #Check if in file
                    print(">>Card Already In Database.\n")
                else:
                    print(">>Card Successfully Entered!\n")
                    #Write to file if valid
                    fw.write("%s:%s," % (cardType, str(newCard)))
                

def main():
    #Verify data file exists, and grab path
    hostDir = verifyFiles()

    #Recieve command
    command = int(input("Please choose an action:\n(1) Enter new cards\n(2) Calculate Values\n"))

    #Check input
    while(command != 1 and command != 2):
        print(">>Invalid Input, Try Again.\n")
        command = int(input("Please choose an action:\n(1) Enter new cards\n(2) Calculate Values\n"))
        
    #Exeggute command
    if(command == 1):
        cardEntry(hostDir)
    else:
        calculateValues(hostDir)
    
main()
