import Ebay
import Logs
from tinydb import TinyDB
import os
import time
import sys

########################################################################################################################
# Search.py
#
# Search has functions dealing with high level searching for items
#
# GenerateSearch("Keyword",(float)StoppingPrice,(int 1/0)AuctionsOnly) Generate search returns a array structure where
# searches between two neighboring numbers will don't exceed 100 pages
# New() Creates a new database under the Searches folder where all search data is saved
# Search("Keywords",(int 1/0)AuctionOnly,[(float)SearchIndex],dbSearches) Accesses the Ebay API to search for items that
# fit the criteria and adds there information to the searches database and returns that data
#
########################################################################################################################


# Generate Search returns a array structure where searches between two neighboring numbers will don't exceed 100 pages
# using the theory of bisection
def GenerateSearch(SearchString,StoppingPrice,AuctionsOnly):

    if(StoppingPrice == 0):  # if no stopping price call absurdly high price from Ebay API
        StoppingPrice = 100000

    SearchPriceChain = [0, float(StoppingPrice)]  # Starting Search Price Chain

    CheckIndex = 1
    while 1:
        # Display information
        printing = "\rSearching %s" % SearchString + " %s" % str(SearchPriceChain) + " "
        while(len(printing) < 70):
            printing = printing + " "
        sys.stdout.write(printing)
        sys.stdout.flush()

        try:  # Call ebay between the price of the current working value and the value before it, calling 100th page
            CheckResponce = Ebay.Call(SearchString, AuctionsOnly, 100, '%.2f' % (SearchPriceChain[CheckIndex]), '%.2f' % (SearchPriceChain[CheckIndex-1]),1)
        except:  # Failed to get a responce from API
            print(CheckIndex)
            print(SearchPriceChain)
            print(SearchString)
            CheckResponce = Ebay.Call(SearchString, AuctionsOnly, 100, '%.2f' % (SearchPriceChain[CheckIndex]),
                                      '%.2f' % (SearchPriceChain[CheckIndex - 1]), 1)

        try:  # Check if ebay api responded with items
            CheckResponceLength = int(CheckResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["@count"])
        except:  # If failed to get length then either out of calls or some error
            print("CheckResponceLengthFailed")
            return None  # Failure, Generic Error

        if (CheckResponceLength == 100):  # If 100th page is completly full of items (100 ct) then bisect
            # Insert number halfway between working number and checking number (working number - 1)
            NewPrice = round((SearchPriceChain[CheckIndex] + SearchPriceChain[CheckIndex - 1]) / 2,2)
            if NewPrice not in SearchPriceChain:  # Make sure inserting number is not currently in the search list, if
                                                  # it is then that means that search has more than 100 pages of 100
                                                  # items in a .01$ search interval
                SearchPriceChain.insert(CheckIndex, NewPrice)
            else:
                CheckIndex = CheckIndex + 1  # If insert number in chain then move onto next number set
        else:  # If there are not 100 items in search move working number to next number in the array
            CheckIndex = CheckIndex + 1

        if (CheckIndex >= len(SearchPriceChain)):  # check if working number is equal to the ammount of numbers in the array
            break

    Logs.Write("Generate Search Index For: " + SearchString + " Returned: " + str(SearchPriceChain))
    return SearchPriceChain  # Success


# New creates a new data base under the searches folder for the search data to be stored in
def New():
    path = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/"
    if not os.path.exists(path):
        os.makedirs(path)

    db = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/" + str(time.time()))


# Search searches the ebay api for items fitting the description
# Note: Search Index is an array of format [(float),...,(float)] in accending order, where it will search between each
# of the numbers
# Success:
# Failure:
def Search(Keywords,AuctionOnly,SearchIndex,dbSearches):

    Data = {}  # Initilize data json data structure
    ItemCount = 0  # Item Count counts the total number of items

    for SearchPriceIndex in range(len(SearchIndex) - 1):  # Searching between top and bottom
        SearchPriceTop = SearchIndex[SearchPriceIndex + 1]
        SearchPriceBottom = SearchIndex[SearchPriceIndex]

        Inserted = []  # Array storing data to be put into the database
        for PageNumber in range(100):  # max page count is 100

            # Display stuff
            printing = "\rSearching for: %s" % str(Keywords) + " between: %s" % str(SearchPriceTop) + " %s" % str(SearchPriceBottom) + " page: %d" % PageNumber
            while (len(printing) < 70):
                printing = printing + " "
            sys.stdout.write(printing)
            sys.stdout.flush()

            PageNumber = PageNumber + 1  # PageNumber starts at 0 and goes to 99 where API's page number goes from 1-100
                                         # Incrimenting before calling is correct since it fixes this issue

            EbayResponce = Ebay.Call(Keywords, AuctionOnly, PageNumber, SearchPriceTop, SearchPriceBottom,1)

            if EbayResponce == None:  # Ebay api call failed
                print("Ebay Responce Failure")
                break  # move onto next item

            Count = int(EbayResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["@count"])

            if(Count > 0):  # If items were recieved
                EbayResponce = EbayResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["item"]
            else:  # If no items were recieved
                print(" blank page recieved check this to see if zero update like 80")
                break  # Move onto next item

            for Item in EbayResponce:
                if '?var' in Item["viewItemURL"][0]:
                    Item["viewItemURL"][0] = Item["viewItemURL"][0].split("?var")[0]
                Item['SearchKeywords'] = str(Keywords)
                Data[ItemCount] = Item

                Inserted.append(Item)  # Store item data in Inserted variable

                ItemCount = ItemCount + 1

            if (Count < 100):  # If a block is not full then all items in the block have been seen
                break

        dbSearches.insert_multiple(Inserted)  # Insert item data into data base

    return Data