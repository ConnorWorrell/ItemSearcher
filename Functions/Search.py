import Ebay
import Logs
from tinydb import TinyDB, Query
import os
import time
import sys
from datetime import  datetime

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

        if (CheckIndex >= len(SearchPriceChain)):# and CheckResponceLength < 100):
            break

    Logs.Write("Generate Search Index For: " + SearchString + " Returned: " + str(SearchPriceChain))
    return SearchPriceChain

def New():
    db = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/" + str(time.time()))

def Search(Keywords,AuctionOnly,SearchIndex,dbSearches):

    Data = {}

    ItemCount = 0
    # DBName = str(max([float(s.replace('.json', '')) for s in os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/Searches/')]))
    # dbSearches = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/" + DBName)




    PreviousTime = time.time()
    EndTime = time.time()
    StartTime = time.time()

    for SearchPriceIndex in range(len(SearchIndex) - 1):


        SearchPriceTop = SearchIndex[SearchPriceIndex + 1]
        SearchPriceBottom = SearchIndex[SearchPriceIndex]

        Inserted = []
        StartTime = time.time()
        for PageNumber in range(100):
            # LoopTime = time.time() - PreviousTime
            # PreviousTime = time.time()
            # if(LoopTime != 0):
            #     print((EndTime-StartTime)/LoopTime)

            #print(PageNumber)

            printing = "\rSearching for: %s" % str(Keywords) + " between: %s" % str(SearchPriceTop) + " %s" % str(SearchPriceBottom) + " page: %d" % PageNumber
            while (len(printing) < 70):
                printing = printing + " "

            sys.stdout.write(printing)
            sys.stdout.flush()

            PageNumber = PageNumber + 1

            EbayResponce = Ebay.Call(Keywords, AuctionOnly, PageNumber, SearchPriceTop, SearchPriceBottom,1)



            #print("sEARCHcOMPLETE")

            if EbayResponce == None:
                print("Ebay Responce Failure")
                break

            Count = int(EbayResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["@count"])

            #print(str(Count) + 'Count \n')

            if(Count > 0):
                EbayResponce = EbayResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["item"]
            else:
                print(" blank page recieved check this to see if zero update like 80")
                #print(int(EbayResponce["findItemsByKeywordsResponse"][0]["searchResult"][0]["@count"]))
                break

            #print(EbayResponce)


            for Item in EbayResponce:
                if '?var' in Item["viewItemURL"][0]:
                    Item["viewItemURL"][0] = Item["viewItemURL"][0].split("?var")[0]
                Item['SearchKeywords'] = str(Keywords)
                Data[ItemCount] = Item

                Inserted.append(Item)

                ItemCount = ItemCount + 1
                #print(ItemCount)

            #print("multiple")

            if (Count < 100):
                break

        dbSearches.insert_multiple(Inserted)
        EndTime = time.time()


    #dbSearches.close()

    return Data