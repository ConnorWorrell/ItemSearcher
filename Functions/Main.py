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

Discount = .7  # Minimum percent of original price, avg of 10$ item will need to be below 7$ if .7 is used
SpecificProductDiscount = 2  # Percent of origional price for items in specific item section

SearchEverything = 0  # 0 If searching only auctions 1 if searching all listings
ReuseSearch = 0  # Use data from previous search instead of generating new search items
StoppingPrice = [50,6.0]  # [Auctions Only, Everything] Max price without shipping
MaxCalls = 0  # Maximum calls per item search

EndingSoon = int(60*60*24*2.2)  # Unix time cutoff for item to be considered ending soon

StoppingPrice = StoppingPrice[SearchEverything]  # Redifine Stopping Price with Search Everything

if(SearchEverything == 1):  # If Searching everything then no limit on items ending soon since most items are buy now
    EndingSoon = int(60*60*24*32)

# Grab search list from Searching file
SearchingFile = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/Searching'
with open(SearchingFile, 'r') as in_file:
    SearchingFileData = json.load(in_file)
Searching = SearchingFileData["Searching"]
SpecificProductSearch = SearchingFileData["SpecificProductSearch"]

#Inilitization of Global Variables
Output = []
OutputSpecific = []
Errors = []
Lot = []
Display = []


# AddToGUI adds items to the Display global variable in the correct format for the GUI to display later
def AddToGUI(Name,SearchName,Price,AvgPrice,ImageURL,PageURL,ComparisonData):
    #Comparison Data in format [[SearchURL1,SearchImage1,Name1,Price1],[SearchURL2,SearchImage2,Name2,Price2],...]
    global Display
    Display.append([Name,SearchName,Price,AvgPrice,ImageURL,PageURL,ComparisonData])


# Total Search searches everything in the Searching Title variable
def TotalSearch(SearchingTitle,SearchNonAuctions):
    global Output
    global OutputSpecific

    DBName = str(max([float(s.replace('.json', '')) for s in
                      os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/Searches/')]))
    dbSearches = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/" + DBName)

    for SearchingNonAuctions in range(SearchNonAuctions+1): # Runs once if only auctions and twice if everything

        if SearchingNonAuctions == 0:  # If Searching auctions
            AuctionSearch = 1  # Searching Auctions
        else:
            AuctionSearch = 0

        SearchList = Search.GenerateSearch(SearchingTitle, StoppingPrice, AuctionSearch)  # Generate search array

        Search.Search(SearchingTitle, AuctionSearch, SearchList,dbSearches)  # Search items in search array


# Analisis evaluates all items in Items List to see if they are deals or not
def Analisis(ItemsList):
    OutOfCalls = 0
    global MaxCalls
    driver = None

    UPCDataBase = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToUPC")
    ShippingDataBase = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToShipping")
    AvgPriceDataBase = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToAvgPrice")
    ErrorsDataBase = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")
    WebDriverPath = os.path.dirname(os.path.dirname(__file__)) + '/Drivers/chromedriver.exe'

    TotalCount = len(ItemsList)  # Total Count of items to search

    if(MaxCalls == 0):  # No maximum call count
        CallCount = len(ItemsList)
    elif MaxCalls > len(ItemsList):  # More calls than items
        CallCount = len(ItemsList)
    else:  # Call count is limited by Maximum calls
        CallCount = MaxCalls

    LastCycle = time.time()*2  # Record cycle time for time predictions
    RecordedCycleTime = []  # Initilize empty time per cycle array
    for Item in range(CallCount):  # For every item
        CycleTime = time.time() - LastCycle  # Calculate time it took for last item to be analized
        RecordedCycleTime.append(CycleTime)  # Keep track of number

        # If more than 300 numbers remove the first number in the list, or if the first number is negative and there is more than one number
        if(len(RecordedCycleTime) > 300 or (RecordedCycleTime[0] < 0 and len(RecordedCycleTime >= 2))):
            RecordedCycleTime = RecordedCycleTime[1:len(RecordedCycleTime)]

        # Calculate expected time remaining in mins
        ExpectedTimeRemaining = statistics.mean(RecordedCycleTime)*(TotalCount-Item)/60
        LastCycle = time.time()  # Record start time for analysis

        # Get Item information
        ItemSearchKeywords = ItemsList[Item]['SearchKeywords']
        ItemURL = ItemsList[Item]['viewItemURL'][0]
        ItemTitle = ItemsList[Item]['title'][0]
        ItemUPC = Get.UPC(ItemURL,UPCDataBase)
        ItemPrice = ItemsList[Item]['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']
        ItemShippingType = ItemsList[Item]['shippingInfo'][0]['shippingType'][0]
        try:
            ItemPicture = ItemsList[Item]['pictureURLSuperSize'][0]
        except:
            try:
                ItemPicture = ItemsList[Item]['galleryURL'][0]
            except:
                ItemPicture = ""
        ItemName = ItemsList[Item]['title'][0]

        #Display stuff
        sys.stdout.write(
            "\rSearching %d" % Item + " of %d" % TotalCount + " " + "Minutes Remainging: %.2f" % ExpectedTimeRemaining + " " + str(ItemTitle) + " ")
        sys.stdout.flush()

        #Calculating Endtime of listing
        ItemEndTime = ItemsList[Item]['listingInfo'][0]['endTime'][0]
        Year = int(ItemEndTime[0:4])
        Month = int(ItemEndTime[5:7])
        Dayy = int(ItemEndTime[8:10])
        Hour = int(ItemEndTime[11:13])
        Minute = int(ItemEndTime[14:16])
        dt = datetime.datetime(Year, Month, Dayy, Hour, Minute, 0)
        UnixEndingStamp = time.mktime(dt.timetuple())

        if(float(UnixEndingStamp) < time.time()):  # Item auction end time has passed
            print('Auction ended already for: ' + str(ItemURL))

        # Get shipping on items where shipping changes for different places
        if ItemShippingType == 'Calculated' or ItemShippingType == 'CalculatedDomesticFlatInternational' or ItemShippingType == 'FreePickup':
            ItemShipping,driver = Get.Shipping(ItemURL,driver,ShippingDataBase,WebDriverPath)
        else:
            try:
                ItemShipping = ItemsList[Item]['shippingInfo'][0]['shippingServiceCost'][0]['__value__']
            except:
                continue

        global Lot
        if('lot' in ItemTitle.lower()):  # If item is clearly a multi item auction
            Info = [float(ItemPrice) + float(ItemShipping), str(ItemURL),str(False)]

            if(Info not in Lot and UnixEndingStamp < time.time()+EndingSoon):
                Lot.append(Info)  # Store item info in Lot variable and in GUI
                Logs.Write("Found Lot Item: " + str(Info))
                AddToGUI(ItemName, '', str(float(ItemPrice)+float(ItemShipping)), '0', ItemPicture, ItemURL, [])
            continue
        else:  # Item is probably a single item
            Prices,FinalSearchName,SearchedItems = Get.AvgPrice(ItemURL,ItemTitle,OutOfCalls,float(ItemPrice) + float(ItemShipping),ItemSearchKeywords,float(UnixEndingStamp),AvgPriceDataBase,ErrorsDataBase,UPCDataBase)

        if(FinalSearchName == None or ItemTitle == None):  # Issues getting specific item names
            print("Error: 24, None type")
            print(FinalSearchName)
            print(ItemTitle)
            print(ItemURL)
            Logs.Write("Error: 24, None type " + str(FinalSearchName) + " " + str(ItemTitle) + " " + str(ItemURL) + " " + str(ItemPrice) + " " + str(ItemShipping))
            continue

        # If multi item auction predicted
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

        if Prices == -1 or Prices == None:  # Error finding avg price
            continue

        if ItemSearchKeywords in SpecificProductSearch:  # If item needs to be evaluated by Specific Product Search
            global SpecificProductDiscount
            SearchingForDiscount = SpecificProductDiscount  # Use Specific Product discount
            # If ending soon, and within discount range
            if (float(Prices) * SearchingForDiscount > float(ItemPrice) + float(ItemShipping)) and UnixEndingStamp < time.time()+EndingSoon and ItemURL not in [ItemInfo[2] for ItemInfo in OutputSpecific]:
                OutputSpecific.append([float(ItemPrice) + float(ItemShipping) , float(Prices) , str(ItemURL), str(FinalSearchName), str(SearchingForDiscount), str(ItemSearchKeywords)])
                AddToGUI(ItemName, FinalSearchName, str(float(ItemPrice)+float(ItemShipping)), Prices, ItemPicture, ItemURL, SearchedItems)
                Logs.Write("Found Discounted Specific Search Item" + str([float(ItemPrice) + float(ItemShipping) , float(Prices) , str(ItemURL), str(FinalSearchName), str(ItemSearchKeywords)]))
        else:  # Use normal discount
            SearchingForDiscount = Discount

            if (float(Prices) * SearchingForDiscount > float(ItemPrice) + float(ItemShipping)) and UnixEndingStamp < time.time()+EndingSoon and ItemURL not in [ItemInfo[2] for ItemInfo in Output]:
                Output.append([float(ItemPrice) + float(ItemShipping) , float(Prices) , str(ItemURL), str(FinalSearchName), str(SearchingForDiscount), str(ItemSearchKeywords)])
                AddToGUI(ItemName, FinalSearchName, str(float(ItemPrice)+float(ItemShipping)), Prices, ItemPicture, ItemURL, SearchedItems)
                Logs.Write("Found Discounted Item" + str([float(ItemPrice) + float(ItemShipping) , float(Prices) , str(ItemURL), str(FinalSearchName), str(ItemSearchKeywords)]))

    try:
        driver.Quit()  # Close driver after complete
    except:
        print('drive.Quit Failed')

if __name__ == "__main__":

    # New logs and ebay directory
    Logs.New()
    Ebay.New()

    dbErrors = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")
    dbErrors.purge_tables()  # Reset Errors Data Base

    SearchText = Searching  # Data to search
    for i in SpecificProductSearch:  # Add all the Specific product search stuff to Seart Text
        SearchText.append(i)

    if(ReuseSearch == 0):  # If getting new search items
        Search.New()
        for SearchingTitleText in SearchText:
            TotalSearch(SearchingTitleText,SearchEverything)

    DBName = str(max([float(s.replace('.json', '')) for s in
                      os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/Searches/')]))
    dbSearches = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/Searches/" + DBName)
    Data = dbSearches.table("_default").all()

    Analisis(Data)  # Analise data

    Output.sort()  # Sort based on price
    OutputSpecific.sort()

    # Get all the errors into one variable
    dbErrors = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")
    dbErrorsTable = dbErrors.table().all()
    for a in range(len(dbErrorsTable)):
        try:
            dbErrorsTable[a]['Price']
        except:
            print(dbErrorsTable[a])

        if(dbErrorsTable[a]["EndTime"] < time.time()+EndingSoon and dbErrorsTable[a]["EndTime"] > time.time()):# + 60*60*17):
            print(dbErrorsTable[a]["EndTime"])
            Errors.append([dbErrorsTable[a]['Price'],str(dbErrorsTable[a]['Error']) + " " + str(dbErrorsTable[a]['ItemLink']) + " " + str([dbErrorsTable[a]['ItemTitle']]) + " " + str([dbErrorsTable[a]['CallText']]) + str(dbErrorsTable[a]["EndTime"]) + " | " + str(dbErrorsTable[a]['SearchKeywords'])])

    for i in OutputSpecific:  # add the Specific items to the main output variable
        Output.append(i)

    # Remove all non ascii characters from Output
    Output = [" ".join([str(word) for word in a]).encode('ascii','ignore').decode() for a in Output]

    Output.append("")  # Add blank line between Single items and lot items

    Lot.sort()  # add lot items to main output variable
    for i in range(len(Lot)):
        Output.append(str(Lot[i][0]) + " " + str(Lot[i][1]) + " " + str(Lot[i][2]))

    Output.append("")  # Add line between lot items and errors

    Errors.sort()  # Sort errors and reformat variable
    ErrorsCombined = [str(E[0]) + " " + str(E[1]) for E in Errors]
    Errors = ErrorsCombined

    for i in Errors:  # remove non ascii characters and add errors to main output variable
        RemovedAscii = i.encode('ascii','ignore').decode()
        if RemovedAscii.split("|")[0] not in [Output[a].split("|")[0] for a in range(len(Output))]:
            Output.append(RemovedAscii)

    # Put headers at the beginning of output variable
    Output.insert(0, str(len(Errors)) + " Errors out of " + str(len(Data)))
    Output.insert(1,"")

    Mail.Send(Output)  # Send Output as mail

    # Save Output to file
    DisplayDataPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/DisplayData.txt'
    with open(DisplayDataPosition, 'w') as out_file:
        json.dump(Display, out_file)

    print("Starting Display")
    Disp.Startup(Display)  # Start GUI
