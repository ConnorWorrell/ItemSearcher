import os
import time
import requests
import json
import Logs
from tinydb import TinyDB, Query
from datetime import datetime
from tinydb.operations import increment

########################################################################################################################
# Ebay.py
#
# Ebay contains two functions: New and Call
#
# New() creates a new folder for all of the call data to be placed in under Logs/Calls
# Call("Keywords",(int 1/0)AuctionOnly,(int 1/100)Page,(float)MaxPrice,(float)MinPrice,(int 1/0)Present)
# Call returns the json data structure from ebay containing item information. If Auction Only is 1 it will only search
# auctions, if it is 0 it will search everything, similarly if Present is 1 it will search only current items and if it
# is 0 it will search all completed items. All items returned will lie within Min and Max Price numbers
#
########################################################################################################################

# Initilization

# Get Ebay Api Key from PasswordsAndSuch File
PasswordsFile = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/PasswordsAndSuch'
with open(PasswordsFile, 'r') as in_file:
    Passwords = json.load(in_file)
SecurityAppName = Passwords['SecurityAppName']

try:
    CallFolder = str(max([float(s.replace('.txt', '')) for s in os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Calls/')]))
    LogPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Calls/' + CallFolder + '/'
except:
    LogPosition = None


# New Function creates a new folder where call data is saved to
def New():
    global LogPosition
    LogPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Calls/' + str(time.time())
    try:
        os.makedirs(LogPosition)
    except:
        print("Folder already exists")
    global CallFolder
    CallFolder = LogPosition


# Call will return a json data structure from the ebay finding api with items in it that fit the inputs
# Success: Success returns json data structure
# Failure: Ran out of connection attempts : None
def Call(Keywords,AuctionOnly,Page,MaxPrice,MinPrice,Present):
    Retries = 5  # Number of call attempts before giving up
    SleepTime = 1  # Time between failed calls (doubles each time)

    global LogPosition # If no call folder exists then create a new one
    if LogPosition == None: New()

    # Database where number of call are recorded
    dbCallCount = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/CallCount")
    Search = Query()

    try:  # Get previous call time from data base
        CallTime = dbCallCount.table("_default").all()[len(dbCallCount.table("_default").all())-1]['Time']
    except:  # Unable to get call time from data base
        CurrentTime = int(time.mktime(datetime.now().timetuple()))
        dbCallCount.insert({'Calls': 0, 'Time': CurrentTime})  # Add call time to data base
        CallTime = CurrentTime

    CurrentDateTime = int(time.mktime(datetime.now().timetuple()))  # Current time
    # Time when calls reset
    NewCallingPerioud = int(time.mktime(datetime.utcfromtimestamp(int(CallTime) + 60*60*16 -60*5).replace(hour = 1).replace(minute=5).replace(second=0).replace(microsecond=0).timetuple()))

    if(CurrentDateTime > NewCallingPerioud):  # If we have passed time when calls reset then were in a new call region
        print("New Time Region")
        CurrentTime = int(time.mktime(datetime.now().timetuple()))
        dbCallCount.insert({'Calls': 0, 'Time': CurrentTime})  # Insert new entry with no calls
        CallTime = CurrentTime

    # Note calls reset 1am mtd, or 8am utc

    if Present == 1:  # Find current items
        OperationName = 'findItemsByKeywords'
    else:  # Find completed items
        OperationName = "findCompletedItems"

    APICALL = 'https://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME=' + str(OperationName) + \
              '&SERVICE-VERSION=1.0.0' \
              '&SECURITY-APPNAME=' + str(SecurityAppName) +  \
              '&RESPONSE-DATA-FORMAT=JSON' \
              '&REST-PAYLOAD' \
              '&keywords=' + str(Keywords) + \
              '&paginationInput.pageNumber=' + str(Page)

    ItemFilterCount = 0
    APICALL = APICALL + \
              '&itemFilter(' + str(ItemFilterCount) + ').name=MaxPrice' \
              '&itemFilter(' + str(ItemFilterCount) + ').value=' + str(MaxPrice) + \
              '&itemFilter(' + str(ItemFilterCount + 1) + ').name=MinPrice' \
              '&itemFilter(' + str(ItemFilterCount + 1) + ').value=' + str(MinPrice)
    ItemFilterCount = ItemFilterCount + 2

    if AuctionOnly == 1:
          APICALL = APICALL + \
                    '&itemFilter(' + str(ItemFilterCount) + ').name=ListingType'\
                    '&itemFilter(' + str(ItemFilterCount) + ').value(0)=AuctionWithBIN' \
                    '&itemFilter(' + str(ItemFilterCount) + ').value(1)=Auction'

    APICALL = APICALL + '&outputSelector=PictureURLSuperSize'  # Request high quality photo

    for retryNumber in range(Retries):  # Number of attempts
        try:
            report = requests.get(APICALL)  # Call API

            if 'HTTP 404 Not Found' in str(report.json()):  # Connection Error
                time.sleep(SleepTime)
                SleepTime = SleepTime * 2  # Exponential backoff and recall
                continue

            # Save report to location
            ReportSaveLocation = LogPosition + str(time.time()) + ".txt"
            with open(ReportSaveLocation, 'w') as APIResponcefile:
                json.dump(report.json(), APIResponcefile)
            APIResponcefile.close()

            Logs.Write("Search Ebay: " + Keywords + " Page: " + str(Page) + " Auction: " + str(
                AuctionOnly) + " Present: " + str(Present) + " Between " + str(MinPrice) + " and " + str(
                MaxPrice) + " at " + str(ReportSaveLocation))

            dbCallCount.update(increment("Calls"), Search.Time == CallTime)  # Incriment Call Count

            return(report.json())  # Success
        except:
            time.sleep(SleepTime)  # If failed to parce data recall with Exponential backoff
            SleepTime = SleepTime * 2

    print("Failed to get api responce")  # ran out of recall attempts
    Logs.Write("Search Ebay Failed: " + Keywords + " Page: " + str(Page) + " Auction: " + str(
        AuctionOnly) + " Present: " + str(Present) + " Between " + str(MinPrice) + " and " + str(
        MaxPrice))
    return None  # Failure
