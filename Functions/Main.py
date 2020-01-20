import Logs
import Ebay
import Search
import Get
import Mail
import Display as Disp
import os
from tinydb import TinyDB
import time
import sys
import datetime
import statistics
import json

Discount = .7

SearchEverything = 0
ReuseSearch = 0
StoppingPrice = [50,6.0]
MaxCalls = 0

StoppingPrice = StoppingPrice[SearchEverything]

EndingSoon = int(60*60*24*2.2)

if(SearchEverything == 1):
    EndingSoon = int(60*60*24*32)

SearchingFile = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/Searching'
with open(SearchingFile, 'r') as in_file:
    SearchingFileData = json.load(in_file)

Searching = SearchingFileData["Searching"]

SpecificProductDiscount = 2
SpecificProductSearch = SearchingFileData["SpecificProductSearch"]

if('dvd' in Searching):
    StoppingPrice = .1
    print('Set price to .1 for search')

Output = []
OutputSpecific = []
Errors = []
Lot = []

Display = []
def AddToGUI(Name,SearchName,Price,AvgPrice,ImageURL,PageURL,ComparisonData):
    #Comparison Data in format [[SearchURL1,SearchImage1,Name1,Price1],[SearchURL2,SearchImage2,Name2,Price2],...]
    global Display
    print([Name,SearchName,Price,AvgPrice,ImageURL,PageURL,ComparisonData])
    print(len(Display))
    print(Display)
    Display.append([Name,SearchName,Price,AvgPrice,ImageURL,PageURL,ComparisonData])

def TotalSearch(SearchingTitle,SearchNonAuctions):
    global Output
    global OutputSpecific

    DBName = str(max([float(s.replace('.json', '')) for s in
                      os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/Searches/')]))
    dbSearches = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/" + DBName)

    for SearchingNonAuctions in range(SearchNonAuctions+1):

        if SearchingNonAuctions == 0:
            AuctionSearch = 1
        else:
            AuctionSearch = 0

        SearchList = Search.GenerateSearch(SearchingTitle, StoppingPrice, AuctionSearch)

        Search.Search(SearchingTitle, AuctionSearch, SearchList,dbSearches)


def Analisis(ItemsList):
    OutOfCalls = 0
    global MaxCalls
    driver = None

    UPCDataBase = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToUPC")
    ShippingDataBase = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToShipping")
    AvgPriceDataBase = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToAvgPrice")
    ErrorsDataBase = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")

    WebDriverPath = os.path.dirname(os.path.dirname(__file__)) + '/Drivers/chromedriver.exe'

    TotalCount = len(ItemsList)

    if(MaxCalls == 0):
        CallCount = len(ItemsList)
    elif MaxCalls > len(ItemsList):
        CallCount = len(ItemsList)
    else:
        CallCount = MaxCalls

    LastCycle = time.time()
    RecordedCycleTime = []
    for Item in range(CallCount):
        CycleTime = time.time() - LastCycle
        RecordedCycleTime.append(CycleTime)

        if(len(RecordedCycleTime) > 300):
            RecordedCycleTime = RecordedCycleTime[1:len(RecordedCycleTime)]


        ExpectedTimeRemaining = statistics.mean(RecordedCycleTime)*(TotalCount-Item)/60
        LastCycle = time.time()

        ItemSearchKeywords = ItemsList[Item]['SearchKeywords']
        ItemURL = ItemsList[Item]['viewItemURL'][0]
        ItemTitle = ItemsList[Item]['title'][0]
        ItemUPC = Get.UPC(ItemURL,UPCDataBase)
        ItemPrice = ItemsList[Item]['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']
        ItemShippingType = ItemsList[Item]['shippingInfo'][0]['shippingType'][0]
        print(ItemsList[Item])
        try:
            ItemPicture = ItemsList[Item]['pictureURLSuperSize'][0]
        except:
            try:
                ItemPicture = ItemsList[Item]['galleryURL'][0]
            except:
                ItemPicture = ""
        ItemName = ItemsList[Item]['title'][0]

        sys.stdout.write(
            "\rSearching %d" % Item + " of %d" % TotalCount + " " + "Minutes Remainging: %.2f" % ExpectedTimeRemaining + " " + str(ItemTitle) + " ")
        sys.stdout.flush()

        ItemEndTime = ItemsList[Item]['listingInfo'][0]['endTime'][0]
        Year = int(ItemEndTime[0:4])
        Month = int(ItemEndTime[5:7])
        Dayy = int(ItemEndTime[8:10])
        Hour = int(ItemEndTime[11:13])
        Minute = int(ItemEndTime[14:16])
        dt = datetime.datetime(Year, Month, Dayy, Hour, Minute, 0)
        UnixEndingStamp = time.mktime(dt.timetuple())

        if(float(UnixEndingStamp) < time.time()):

            print('Auction ended already for: ' + str(ItemURL))

        if ItemShippingType == 'Calculated' or ItemShippingType == 'CalculatedDomesticFlatInternational' or ItemShippingType == 'FreePickup':
            ItemShipping,driver = Get.Shipping(ItemURL,driver,ShippingDataBase,WebDriverPath)
        else:
            try:
                ItemShipping = ItemsList[Item]['shippingInfo'][0]['shippingServiceCost'][0]['__value__']
            except:
                continue

        global Lot
        if('lot' in ItemTitle.lower()):

            Info = [float(ItemPrice) + float(ItemShipping), str(ItemURL),str(False)]

            if(Info not in Lot and UnixEndingStamp < time.time()+EndingSoon):
                Lot.append(Info)
                Logs.Write("Found Lot Item: " + str(Info))
                AddToGUI(ItemName, '', str(float(ItemPrice)+float(ItemShipping)), '0', ItemPicture, ItemURL, [])
            continue
        else:
            Prices,FinalSearchName,SearchedItems = Get.AvgPrice(ItemURL,ItemTitle,OutOfCalls,float(ItemPrice) + float(ItemShipping),ItemSearchKeywords,float(UnixEndingStamp),AvgPriceDataBase,ErrorsDataBase,UPCDataBase)

        print(Prices)

        if(FinalSearchName == None or ItemTitle == None):
            print("Error: 24, None type")
            print(FinalSearchName)
            print(ItemTitle)
            print(ItemURL)
            Logs.Write("Error: 24, None type " + str(FinalSearchName) + " " + str(ItemTitle) + " " + str(ItemURL) + " " + str(ItemPrice) + " " + str(ItemShipping))
            continue

        if(('collection' in ItemTitle.lower() or 'collection' in FinalSearchName or 'Multi Item Auction Found' == FinalSearchName) and Prices <= 0):
            Info = [float(ItemPrice) + float(ItemShipping), str(ItemURL), str('Multi Item Auction Found' == FinalSearchName)]

            if (Info not in Lot and UnixEndingStamp < time.time() + EndingSoon):
                Lot.append(Info)
                Logs.Write("Found Lot Item: " + str(Info))
                AddToGUI(ItemName, FinalSearchName, str(float(ItemPrice)+float(ItemShipping)), '0', ItemPicture, ItemURL, [])
            continue

        if(Prices == -2): #Out of calls
            OutOfCalls = 1
            continue

        if Prices == -1 or Prices == None:
            continue

        if ItemSearchKeywords in SpecificProductSearch:
            global SpecificProductDiscount
            SearchingForDiscount = SpecificProductDiscount
            if (float(Prices) * SearchingForDiscount > float(ItemPrice) + float(ItemShipping)) and UnixEndingStamp < time.time()+EndingSoon and ItemURL not in [ItemInfo[2] for ItemInfo in OutputSpecific]:
                OutputSpecific.append([float(ItemPrice) + float(ItemShipping) , float(Prices) , str(ItemURL), str(FinalSearchName), str(SearchingForDiscount), str(ItemSearchKeywords)])
                AddToGUI(ItemName, FinalSearchName, str(float(ItemPrice)+float(ItemShipping)), Prices, ItemPicture, ItemURL, SearchedItems)
                Logs.Write("Found Discounted Specific Search Item" + str([float(ItemPrice) + float(ItemShipping) , float(Prices) , str(ItemURL), str(FinalSearchName), str(ItemSearchKeywords)]))
        else:
            SearchingForDiscount = Discount

            if (float(Prices) * SearchingForDiscount > float(ItemPrice) + float(ItemShipping)) and UnixEndingStamp < time.time()+EndingSoon and ItemURL not in [ItemInfo[2] for ItemInfo in Output]:
                Output.append([float(ItemPrice) + float(ItemShipping) , float(Prices) , str(ItemURL), str(FinalSearchName), str(SearchingForDiscount), str(ItemSearchKeywords)])
                AddToGUI(ItemName, FinalSearchName, str(float(ItemPrice)+float(ItemShipping)), Prices, ItemPicture, ItemURL, SearchedItems)
                Logs.Write("Found Discounted Item" + str([float(ItemPrice) + float(ItemShipping) , float(Prices) , str(ItemURL), str(FinalSearchName), str(ItemSearchKeywords)]))

    try:
        driver.Quit()
    except:
        print('drive.Quit Failed')

if __name__ == "__main__":

    Logs.New()
    Ebay.New()

    dbErrors = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")
    dbErrors.purge_tables()

    SearchText = Searching
    for i in SpecificProductSearch:
        SearchText.append(i)

    if(ReuseSearch == 0):
        Search.New()
        for SearchingTitleText in SearchText:
            TotalSearch(SearchingTitleText,SearchEverything)

    DBName = str(max([float(s.replace('.json', '')) for s in
                      os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/Searches/')]))
    dbSearches = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/" + DBName)
    Data = dbSearches.table("_default").all()

    Analisis(Data)

    Output.sort()
    OutputSpecific.sort()

    dbErrors = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")

    dbErrorsTable = dbErrors.table().all()

    for a in range(len(dbErrorsTable)):
        try:
            dbErrorsTable[a]['Price']
        except:
            print(dbErrorsTable[a])

    for a in range(len(dbErrorsTable)):
        if(dbErrorsTable[a]["EndTime"] < time.time()+EndingSoon and dbErrorsTable[a]["EndTime"] > time.time()):# + 60*60*17):
            print(dbErrorsTable[a]["EndTime"])
            Errors.append([dbErrorsTable[a]['Price'],str(dbErrorsTable[a]['Error']) + " " + str(dbErrorsTable[a]['ItemLink']) + " " + str([dbErrorsTable[a]['ItemTitle']]) + " " + str([dbErrorsTable[a]['CallText']]) + str(dbErrorsTable[a]["EndTime"]) + " | " + str(dbErrorsTable[a]['SearchKeywords'])])

    for i in OutputSpecific:
        Output.append(i)

    Output = [" ".join([str(word) for word in a]).encode('ascii','ignore').decode() for a in Output]

    Output.append("")

    Lot.sort()
    print(Lot)
    for i in range(len(Lot)):
        Output.append(str(Lot[i][0]) + " " + str(Lot[i][1]) + " " + str(Lot[i][2]))

    Output.append("")

    Errors.sort()

    ErrorsCombined = [str(E[0]) + " " + str(E[1]) for E in Errors]
    Errors = ErrorsCombined

    for i in Errors:
        RemovedAscii = i.encode('ascii','ignore').decode()
        if RemovedAscii.split("|")[0] not in [Output[a].split("|")[0] for a in range(len(Output))]:
            Output.append(RemovedAscii)

    Output.insert(0, str(len(Errors)) + " Errors out of " + str(len(Data)))
    Output.insert(1,"")

    Mail.Send(Output)

    print(Display)

    DisplayDataPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/DisplayData.txt'
    with open(DisplayDataPosition, 'w') as out_file:
        json.dump(Display, out_file)

    print("Starting Display")
    Disp.Startup(Display)
