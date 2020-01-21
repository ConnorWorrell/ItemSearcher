import os
import time
import requests
import json
import Logs
from tinydb import TinyDB, Query
from datetime import datetime
from tinydb.operations import increment

PasswordsFile = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/PasswordsAndSuch'
with open(PasswordsFile, 'r') as in_file:
    Passwords = json.load(in_file)

SecurityAppName = Passwords['SecurityAppName']

def New():
    LogPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Calls/' + str(time.time())
    print(LogPosition)
    try:
        os.makedirs(LogPosition)
    except:
        print("Folder already exists")

def Call(Keywords,AuctionOnly,Page,MaxPrice,MinPrice,Present):
    Retries = 5
    SleepTime = 1

    CallFolder = str(max([float(s.replace('.txt', '')) for s in os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Calls/')]))

    dbCallCount = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/CallCount")
    Search = Query()

    try:
        CallTime = dbCallCount.table("_default").all()[len(dbCallCount.table("_default").all())-1]['Time']
    except:
        CurrentTime = int(time.mktime(datetime.now().timetuple()))
        dbCallCount.insert({'Calls': 0, 'Time': CurrentTime})
        CallTime = CurrentTime

    CurrentDateTime = int(time.mktime(datetime.now().timetuple()))
    NewCallingPerioud = int(time.mktime(datetime.utcfromtimestamp(int(CallTime) + 60*60*16 -60*5).replace(hour = 1).replace(minute=5).replace(second=0).replace(microsecond=0).timetuple()))

    if(CurrentDateTime > NewCallingPerioud):
        print("New Time Region")
        CurrentTime = int(time.mktime(datetime.now().timetuple()))
        dbCallCount.insert({'Calls': 0, 'Time': CurrentTime})
        CallTime = CurrentTime

    # Note calls reset 1am mtd, or 8am utc

    if Present == 1:
        APICALL = 'https://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME=findItemsByKeywords' \
                  '&SERVICE-VERSION=1.0.0' \
                  '&SECURITY-APPNAME=' + SecurityAppName +  \
                  '&RESPONSE-DATA-FORMAT=JSON' \
                  '&REST-PAYLOAD' \
                  '&keywords=' + Keywords + \
                  '&paginationInput.pageNumber=' + str(Page)
    else:
        APICALL = 'https://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME=findCompletedItems' \
                  '&SERVICE-VERSION=1.0.0' \
                  '&SECURITY-APPNAME=' + SecurityAppName +  \
                  '&RESPONSE-DATA-FORMAT=JSON' \
                  '&REST-PAYLOAD' \
                  '&keywords=' + Keywords + \
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
