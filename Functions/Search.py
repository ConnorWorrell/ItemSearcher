import Ebay
import Logs
from tinydb import TinyDB
import os
import time
import sys

def GenerateSearch(SearchString,StoppingPrice,AuctionsOnly):

    if(StoppingPrice == 0):
        StoppingPrice = 100000

    SearchPriceChain = [0, float(StoppingPrice)]


    CheckIndex = 1
    while 1:
        printing = "\rSearching %s" % SearchString + " %s" % str(SearchPriceChain) + " "
        while(len(printing) < 70):
            printing = printing + " "
        sys.stdout.write(printing)
        sys.stdout.flush()
        try:
            CheckResponce = Ebay.Call(SearchString, AuctionsOnly, 100, '%.2f' % (SearchPriceChain[CheckIndex]), '%.2f' % (SearchPriceChain[CheckIndex-1]),1)
        except:
            print(CheckIndex)
            print(SearchPriceChain)
            print(SearchString)
            CheckResponce = Ebay.Call(SearchString, AuctionsOnly, 100, '%.2f' % (SearchPriceChain[CheckIndex]),
                                      '%.2f' % (SearchPriceChain[CheckIndex - 1]), 1)
        try:
            CheckResponceLength = int(CheckResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["@count"])
        except:
            print("CheckResponceLengthFailed")
            return None

        if (CheckResponceLength == 100):
            NewPrice = round((SearchPriceChain[CheckIndex] + SearchPriceChain[CheckIndex - 1]) / 2,2)
            if NewPrice not in SearchPriceChain:
                SearchPriceChain.insert(CheckIndex, NewPrice)
            else:
                CheckIndex = CheckIndex + 1
        else:
            CheckIndex = CheckIndex + 1

        if (CheckIndex >= len(SearchPriceChain)):
            break

    Logs.Write("Generate Search Index For: " + SearchString + " Returned: " + str(SearchPriceChain))
    return SearchPriceChain

def New():
    path = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/"
    if not os.path.exists(path):
        os.makedirs(path)

    db = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/" + str(time.time()))

def Search(Keywords,AuctionOnly,SearchIndex,dbSearches):

    Data = {}

    ItemCount = 0

    for SearchPriceIndex in range(len(SearchIndex) - 1):


        SearchPriceTop = SearchIndex[SearchPriceIndex + 1]
        SearchPriceBottom = SearchIndex[SearchPriceIndex]

        Inserted = []
        for PageNumber in range(100):

            printing = "\rSearching for: %s" % str(Keywords) + " between: %s" % str(SearchPriceTop) + " %s" % str(SearchPriceBottom) + " page: %d" % PageNumber
            while (len(printing) < 70):
                printing = printing + " "

            sys.stdout.write(printing)
            sys.stdout.flush()

            PageNumber = PageNumber + 1

            EbayResponce = Ebay.Call(Keywords, AuctionOnly, PageNumber, SearchPriceTop, SearchPriceBottom,1)

            if EbayResponce == None:
                print("Ebay Responce Failure")
                break

            Count = int(EbayResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["@count"])

            if(Count > 0):
                EbayResponce = EbayResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["item"]
            else:
                print(" blank page recieved check this to see if zero update like 80")
                break

            for Item in EbayResponce:
                if '?var' in Item["viewItemURL"][0]:
                    Item["viewItemURL"][0] = Item["viewItemURL"][0].split("?var")[0]
                Item['SearchKeywords'] = str(Keywords)
                Data[ItemCount] = Item

                Inserted.append(Item)

                ItemCount = ItemCount + 1

            if (Count < 100):
                break

        dbSearches.insert_multiple(Inserted)

    return Data