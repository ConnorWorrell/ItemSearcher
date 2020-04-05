import requests
# from tinydb import Query
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import re
import Logs
import Ebay
import statistics
import os
import json
import DataBaseCustom as DB

########################################################################################################################
# Get.py
#
# Get contains functions relating to getting information from web or caches
#
# UPC("ItemURL",UPCDataBase) Gets Upc code from a database or a URL if it is not found
# Shipping("ItemURL",driver,ShippingDataBase,WebDriverPath) Shipping gets the price of shipping from a database or a
# URL if it is not found
# AvgPrice("ItemURL",Title,OutOfCalls,Price,ErrorAppendSearchKeywords,EndTime,AVGPriceDB,ErrorsDB,UPCDataBase)
# AvgPrice gets the average price of sold items sharing the same UPC or a similar Title from a database or a URL if
# it is not found
# TitleToSearch ("Title",URL=None) returns a simplified version of a Title
#
########################################################################################################################

# Initilization

# Load the json file stored in Database/PasswordsAndSuch
PasswordsFile = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/PasswordsAndSuch'
with open(PasswordsFile, 'r') as in_file:
    Passwords = json.load(in_file)

# Get information out of json file
ReceivingZipCode = Passwords['ReceivingZipCode']


# UPC Gets UPC code from a database or a URL if it is not found, UPCDataBase is the database that stores information to
# convert URLs to UPCs
# Success: returns UPC Code ie: "1234567890"
# Failure: returns -1
def UPC(ItemLink,UPCDataBase = None):
    Retries = 5  # Number of times that getting the UPC will be attempted before giving up
    SleepTime = 1  # Time in seconds to delay between failed attempts (doubling each attempt)

    ItemLink = ItemLink.split('?')[0]  # Remove un-needed information from URL link

    # db = UPCDataBase
    # User = Query()

    # Search = db.search(User.Link == ItemLink)  # Search for URL in database

    Search = DB.FindUPCDataBase({"Link":ItemLink})

    if(Search != []):  # If search returns something return database UPC
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Cache: " + str(Search[0]['UPC']))
        return Search[0]['UPC']

    page = None

    for RetryNumber in range(Retries):  # Retry attempts
        try:
            page = requests.get(ItemLink)  # Get page data
        except:
            # If unable to get data wait and try again
            print("Connection Error, Retrying in " + str(SleepTime) + " seconds")
            time.sleep(SleepTime)  # wait before trying to fetch the data again
            SleepTime *= 2  # Exponential backoff

    if(page == None):  # If failed to get connection after running out of attempts
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Error: Unable to resolve connection error after 5 attempts")
        return None

    # Parce data recieved
    soup = BeautifulSoup(page.text, 'html.parser')
    UPC_Find = soup.find(itemprop="gtin13")

    if (UPC_Find == None): # If page didn't include UPC information
        UPC = -1 # Failure to get UPC code
        DB.AddUPCDataBase({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
        # db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: No UPC")
        return UPC  # Failure to find UPC

    UPC = UPC_Find.contents[0]
    if (UPC.isdigit() == False): # If page found UPC code but it dosen't match up with expected codes
        UPC = -1 # Failure to get UPC Code
        DB.AddUPCDataBase({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
        # db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: No UPC")
        return UPC  # Failure to find UPC

    # UPC is found and it is in expected format
    # Place UPC into database
    DB.AddUPCDataBase({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
    # db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})

    Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: " + str(UPC))
    return UPC  # Success finding UPC


# Shipping gets shipping price from a database using the URL and if it's not in the database then it attempts to find
# it online
# driver is the browser driver that is being used and it is provided and returned by the function so that it is not
# necessary to restart the browser every time
# Success: Free Shipping : 0, Found Shipping Price: (float)
# Failure: Generic Error : -1, check Logs for more information
def Shipping(ItemLink,driver,WebDriverPath,ShippingDataBase = None):
    WaitTimeBetweenButtons = .1 # Wait time between character inserts when typing in zip code
    global ReceivingZipCode
    zipCode = ReceivingZipCode # Zip code of receiving location for calculating shipping
    Retries = 5  # Number of times that scraping will be attempted before giving up
    TimeoutTime = .5  # Time given to web driver to load before interacting with page

    ItemLink = ItemLink.split('?')[0]  # Remove un-necessary information from URL

    # db = ShippingDataBase
    # User = Query()

    Logs.Write("Starting Getting Shipping for " + ItemLink)

    Search = DB.FindShippingDataBase({"Link":ItemLink})
    # Search = db.search(User.Link == ItemLink)  # Look in database for shipping information
    if (Search != []):  # If shipping information is found in database
        Logs.Write("Get Shipping From Item Link: " + ItemLink + " Cache: " + str(Search[0]['Shipping']))
        return Search[0]['Shipping'],driver # Success, found in database

    for i in range(Retries):  # Number of attempts

        time.sleep(  # Wait for page to load before interacting
            1 + random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        TimeoutTime = TimeoutTime * 2  # If failed to scrape double the timeout
        try:  # Loading page, restarting driver if its closed
            driver.get(ItemLink)
        except:
            driver = webdriver.Chrome(executable_path=WebDriverPath)
            driver.get(ItemLink)

        time.sleep(  # Wait for page to load before interacting
            1 + random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        if(driver.current_url != ItemLink):
            print("URL's dont match" + driver.current_url + "  |  " + ItemLink)
            continue

        try:  # Check for item having ended way 1
            MissingListing1 = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "w3" + '"]/div/div/div/div/span/span'))).text
            if ("The listing you're looking for has ended." in MissingListing1):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item Auction Ended")
                DB.AddShippingDataBase({'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                # db.insert(
                #     {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1,driver  # Failure, item listing has ended
        except:  # Passes check
            pass

        try:  # Check for item having ended way 2
            MissingListing2 = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "mainContent-w0-w0-0" + '"]/div/div/span'))).text
            if("The listing you're looking for has ended." in MissingListing2):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item Auction Ended")
                DB.AddShippingDataBase({'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                # db.insert(
                #     {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1, driver  # Failure, item listing has ended
        except:  # Passes Check
            pass

        try:  # Check shipping to usa
            ShippingText = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "vi-acc-shpsToLbl-cnt" + '"]/span'))).text
            if('Worldwide' not in ShippingText and 'United States' not in ShippingText):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item does not ship to US")
                DB.AddShippingDataBase({'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                # db.insert(
                #     {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1, driver  # Failure, item does not ship to the USA
            # Passes check, does ship to USA
        except:  # Unable to find item, reloading page
            continue

        try:  # Click shipping and payments button
            WebDriverWait(driver, TimeoutTime).until(
                EC.element_to_be_clickable((By.ID, "viTabs_1"))).click()
        except:
            continue
        time.sleep(  # Wait for webpage to respond
             random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        try:  # Check if seller specified shipping
            text = str(WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="' + "shCost-err" + '"]'))).text)
            if "seller has not specified shipping options" in text:
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Unspecified Shipping")
                DB.AddShippingDataBase({'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                # db.insert(
                #     {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1, driver  # Seller did not pick a shipping option
            # Seller picked a shipping option
        except:
            pass  # Could not locate element, seller probably specified shipping

        CurrentZipCode = driver.find_element(By.ID,"shZipCode").get_attribute("value")

        if(CurrentZipCode != zipCode):
            # Type zipcode into zipcode box
            for zipCodeLetterIndex in range(len(zipCode)):
                try:
                    WebDriverWait(driver, TimeoutTime).until(  # Type letter
                        EC.element_to_be_clickable((By.ID, "shZipCode"))).send_keys(zipCode[zipCodeLetterIndex])
                except:  # Unable to place letter reloading page
                    continue
                time.sleep(  # Wait between letters (Technically unnecessary but makes it look like typing is more natural)
                    random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2))

            try:  # Click submit button for zip code
                WebDriverWait(driver, TimeoutTime).until(EC.element_to_be_clickable((By.ID, "shGetRates"))).click()
            except:
                continue
            time.sleep(  # Wait for page to reload after submit is clicked
                2 + random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        try:  # Read pricing data
            ShippingInfoRaw = str(WebDriverWait(driver, TimeoutTime).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="' + "shippingSection" + '"]/table/tbody'))).text)
        except:  # Could not find pricing data reloading page
            continue

        if ('Free shipping' in ShippingInfoRaw):  # Check for free shipping
            Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Free Shipping")
            DB.AddShippingDataBase({'Link': ItemLink, 'Shipping': 0, 'Raw': ShippingInfoRaw, "Time": time.time()})
            # db.insert({'Link': ItemLink, 'Shipping': 0, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return 0,driver  # Success, item has free shipping

        if ('US' not in ShippingInfoRaw[0:5]):  # Check for currency that is not USD
            Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Shipping Price In Forien Currency: " + str(ShippingInfoRaw))
            DB.AddShippingDataBase({'Link': ItemLink, 'Shipping': -1, 'Raw': ShippingInfoRaw, "Time": time.time()})
            # db.insert({'Link': ItemLink, 'Shipping': -1, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return -1,driver  # Failure, item does not use us currency

        OutputPrice = re.findall("\d+\.\d+", str(ShippingInfoRaw))  # Match float string to text

        if (OutputPrice != []):  # If found string matching a price
            OutputShippingPrice = min([float(a) for a in OutputPrice])
            Logs.Write(
                "Get Shipping From Item Link: " + ItemLink + " Returned: " + str(
                    OutputShippingPrice))
            DB.AddShippingDataBase({'Link': ItemLink, 'Shipping': OutputShippingPrice, 'Raw': ShippingInfoRaw, "Time": time.time()})
            # db.insert({'Link': ItemLink, 'Shipping': OutputShippingPrice, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return OutputShippingPrice,driver  # Success, found shipping price

    DB.AddShippingDataBase({'Link': ItemLink, 'Shipping': -1, 'Raw': None, "Time": time.time()})
    # db.insert({'Link': ItemLink, 'Shipping': -1, 'Raw': None, "Time": time.time()})
    return -1,driver  # Failed after number of attempts


# AvgPrice takes an ItemURL and returns an approximate average price from a database or from the web
# Note: 3 identical sections of code that could be condensed
# Success: (float), Found new avg price, Found cached avg price, Could not find new avg price but had old avg price
# Failure: Multi Item Auction Predicted : -1, Out Of Calls : -2, No items found : -1, No items sold : -1
def AvgPrice(ItemLink,Title,OutOfCalls,Price,ErrorAppendSearchKeywords,EndTime,ErrorsDB=None,AVGPriceDB=None,UPCDataBase=None,ImageURL = ""):
    CurrentErrorRevision = 4 # Stored in database incase new things need to be added
    Recalling = None

    # db = AVGPriceDB
    # dbErrors = ErrorsDB

    # User = Query()

    if(ItemLink == None):  # If no item link is given
        TitleSearch = Title  # Searching based on title
        UPCCode = -1
        CallText = TitleSearch
    else:  # Item link is given
        UPCCode = UPC(ItemLink)  # Grab UPC of item
        TitleSearch = TitleToSearch(Title,URL=ItemLink)  # Grab simplified title to search by
        CallText = TitleSearch

    if("Multi Item Auction Found" in TitleSearch):  # If TitleToSearch predicts the auction has multiple items in it
        return -1,TitleSearch,[]  # Failure, avg price is inconsistent for multi item sales

    Search = DB.FindAvgDataBase({"CallText":CallText})
    # Search = db.search(User.CallText == CallText)  # Check if avg price is in database

    # print(Search)

    if (Search != []):  # If avg price Cached grab from database
        RecallTime = float(60 * 60 * 24 * 7)  # Time between when avg price is stored to next time it is updated

        try:  # Make sure that avg price has ErrorRevision and SearchedItems keywords
            Search[0]["ErrorRevision"]
            Search[0]['SearchedItems']
        except:  # if it does not then
            Recalling = 1  # Recall the avg price
            print("Missing Revision")
            try:
                DB.RemoveAvgDataBase({"CallText":CallText})
                # db.remove(User.CallText == CallText)  # Remove the item from the database
            except:
                DB.RemoveAvgDataBase({"Link": CallText})
                # db.remove(User.Link == CallText)  # Remove the item from the database

        # Check if it should recalling AVG Price for Item with previous avg price
        if (Recalling == None and float(Search[0]["Time"]) + RecallTime < time.time() and Search[0]['AvgPrice'] > 0):
            Logs.Write("Recalling AVG Price for Item with previous avg price: " + str(str(CallText)))
            Recalling = 1

        # Check if it should recall avg price for item without previous avg price
        elif (Recalling == None and float(Search[0]["Time"]) + RecallTime < time.time() and Search[0]['AvgPrice'] < 0):
            Logs.Write("Recalling AVG Price for Item without previous avg price: " + str(str(CallText)))
            Recalling = 0

        # Check if error revision number is the correct number, if it is then the cached avg price is still valid
        elif(Recalling == None and Search[0]["ErrorRevision"] == CurrentErrorRevision and float(Search[0]['AvgPrice']) > 0):
            Logs.Write("Get AVG Price from UPC: " + str(CallText) + " Cache: " + str(Search[0]['AvgPrice']))
            # print("Avg Price Cached")
            return Search[0]['AvgPrice'], CallText,Search[0]['SearchedItems']  # Success, cached price

        if(len(Search) > 1):  # If multiple items are found, this mean a mistake occured and duplicate
                              # entries in the data base exist
            print("Search is greater than 1, this is a problem: " + str(Search))
            print([ItemLink,Title,OutOfCalls,Price,ErrorAppendSearchKeywords,EndTime])

            for i in range(len(Search)):  # Remove duplicate entries and recall
                try:
                    DB.RemoveAvgDataBase({"CallText": CallText})
                    # db.remove(User.CallText == CallText)
                    print("Removed Extra Text")
                    Recalling = 0
                except:
                    DB.RemoveAvgDataBase({"Link": CallText})
                    # db.remove(User.Link == CallText)
                    print("Removed Extra Link")

        try:
            # If not recalling and error revision number is incorrect remove item from database

            if(Recalling == None and Search[0]["ErrorRevision"] != CurrentErrorRevision):
                print("Removed incorrect error revision number")
                DB.RemoveAvgDataBase({"CallText": CallText})
                # db.remove(User.CallText == CallText)

            # If not recalling and cached avg price was -1 (Error or Unable to find price)
            elif(Recalling == None and Search[0]['AvgPrice'] < 0):
                ErrorCode = Search[0]  # Mix item specific information into database information and return
                ErrorCode['SearchKeywords'] = ErrorAppendSearchKeywords
                ErrorCode["EndTime"] = EndTime
                ErrorCode["ItemLink"] = ItemLink
                ErrorCode["ImageURL"] = ImageURL

                DB.AddErrorsDataBase(ErrorCode)
                # dbErrors.insert(ErrorCode)
                return Search[0]['AvgPrice'],CallText,Search[0]['SearchedItems']  # Success, returning previous Failure

        except:  # If something failed with the databases then recall, remove item if it has the wrong error revision
            if (Recalling == None and Search[0]["ErrorRevision"] != CurrentErrorRevision):
                print("Removed2")

                DB.RemoveAvgDataBase({"Link": CallText})
                # db.remove(User.Link == CallText)


    if(OutOfCalls == 1):  # If out of calls
        print("Repeat Out Of Calls")
        return -2,None,[]  # Failed, Out of calls

    Prices = []
    SearchedItems = []

    Count = 0  # Number of comparison responses if searching based on title
    Count1 = 0  # Number of comparison responses when searching both UPC and Title based on UPC Code
    Count2 = 0  # Number of comparison responses when searching both UPC and Title based on Title

    if(CallText == TitleSearch):  # Only calling Title search
        Responce = Ebay.Call(CallText,0,1,10000,0,0) # Call Title Search
        try:
            Count = int(Responce['findCompletedItemsResponse'][0]['searchResult'][0]['@count']) # Number of items found
        except:
            print(CallText)  # If unable to get Count from responce
            if ('Keyword or category ID are required.' in str(Responce)):
                print('Keyword or category ID are required')
                DB.AddAvgDataBase({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(),
                           "Error": "Keyword or category ID are required", "ErrorRevision": CurrentErrorRevision,
                           "ItemLink": ItemLink, "Price": Price})
                # db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(),
                #            "Error": "Keyword or category ID are required", "ErrorRevision": CurrentErrorRevision,
                #            "ItemLink": ItemLink, "Price": Price})
                return -1, None,[]  # Failure

            print("Used All Calls" + str(Responce))
            return -2, None,[] # Failure, Used All Calls

        for Index in range(Count):  # Build Searched Items based on Returned items
            Item = Responce['findCompletedItemsResponse'][0]['searchResult'][0]['item'][Index]
            if (Item['sellingStatus'][0]['sellingState'][0] == 'EndedWithSales'):
                # If item was sold it counts, otherwise we ignore it
                # Add it to prices and SearchedItems
                Prices.append(float(Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']))
                try:
                    SearchedItems.append([Item['viewItemURL'][0], Item['pictureURLSuperSize'][0], Item['title'][0],
                                      Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']])
                except:
                    try:
                        SearchedItems.append([Item['viewItemURL'][0], Item['galleryURL'][0], Item['title'][0],
                                          Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']])
                    except:
                        SearchedItems.append([Item['viewItemURL'][0], "", Item['title'][0],
                                              Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']])

    else:  # Calling both Title and UPC Search and comparing the two
        # Identical to above
        print("Calling both UPC and Title")
        Responce1 = Ebay.Call(UPCCode,0,1,10000,0,0)  # Responce for UPC Call
        try:
            Count1 = int(Responce1['findCompletedItemsResponse'][0]['searchResult'][0]['@count'])
            if(Count1 == 0):
                print('Nothing found')
            for Index in range(Count1):
                Item = Responce1['findCompletedItemsResponse'][0]['searchResult'][0]['item'][Index]
                if (Item['sellingStatus'][0]['sellingState'][0] == 'EndedWithSales'):
                    print(Item)
                    Prices.append(float(Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']))
                    print("fjdksl " + str([Item['viewItemURL'][0], Item['pictureURLSuperSize'][0], Item['title'][0],
                                          Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']]))
                    try:
                        SearchedItems.append([Item['viewItemURL'][0], Item['pictureURLSuperSize'][0], Item['title'][0],
                                              Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']])
                    except:
                        try:
                            SearchedItems.append([Item['viewItemURL'][0], Item['galleryURL'][0], Item['title'][0],
                                                  Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']])
                        except:
                            SearchedItems.append([Item['viewItemURL'][0], "", Item['title'][0],
                                                  Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']])
                    print('Searched Items2' + str(SearchedItems))
        except:
            pass


        if(Prices == []):  # If UPC Call returned nothing then call for Title
            # Identical to above
            Responce2 = Ebay.Call(TitleSearch, 0, 1, 10000, 0, 0)
            try:
                Count2 = int(Responce2['findCompletedItemsResponse'][0]['searchResult'][0]['@count'])
                for Index in range(Count2):
                    Item = Responce2['findCompletedItemsResponse'][0]['searchResult'][0]['item'][Index]
                    if (Item['sellingStatus'][0]['sellingState'][0] == 'EndedWithSales'):
                        print(Item)
                        Prices.append(float(Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']))
                        #[[SearchURL1,SearchImage1,Name1,Price1],[SearchURL2,SearchImage2,Name2,Price2],...]
                        try:
                            SearchedItems.append(
                                [Item['viewItemURL'][0], Item['pictureURLSuperSize'][0], Item['title'][0],
                                 Item['sellingStatus'][0]['convertedCurrentPrice'][0]['__value__']])
                        except:
                            try:
                                SearchedItems.append([Item['viewItemURL'][0], Item['galleryURL'][0], Item['title'][0],
                                                      Item['sellingStatus'][0]['convertedCurrentPrice'][0][
                                                          '__value__']])
                            except:
                                SearchedItems.append([Item['viewItemURL'][0], "", Item['title'][0],
                                                      Item['sellingStatus'][0]['convertedCurrentPrice'][0][
                                                          '__value__']])
                        print('Searched Items3' + str(SearchedItems))
            except:
                pass

    if (Recalling == 1 and Prices != []):  # If recalling item with previous avg price and new avg price found
        DB.RemoveAvgDataBase({"CallText": CallText})
        # db.remove(User.CallText == CallText)  # remove previous avg price
        print("Recalling: " + str(Search[0]))
    elif(Recalling == 1):  # If recalling item with previous avg price but no new avg price found
        print("Had Past price for item, but couldn't find new price: " + str(Search[0]))

        try:  # Make sure that previous search had Searched Items
            Search[0]['SearchedItems']
            SearchedItemsKeyErrorFailure=0
        except:  # If previous search did not have Searched items then remove it from the data base
            SearchedItemsKeyErrorFailure=1
            DB.RemoveAvgDataBase({"CallText": CallText})
            # db.remove(User.CallText == CallText)
        if(SearchedItemsKeyErrorFailure == 0):  # If previous search had searched items then
            NewCall = Search[0]  # refresh search in database, wait another time period before searching again
            NewCall["Time"] = time.time()
            DB.RemoveAvgDataBase({"CallText": CallText})
            # db.remove(User.CallText == CallText)
            DB.AddAvgDataBase(NewCall)
            # db.insert(NewCall)

            return Search[0]['AvgPrice'],CallText,Search[0]['SearchedItems']  # Success, returned old avg price

    elif(Recalling == 0):  # If recalling item with no previous average price, then remove db entry
        DB.RemoveAvgDataBase({"CallText": CallText})
        # db.remove(User.CallText == CallText)

    if Count == 0 and (Count1 == 0 and Count2 == 0):  # If no items were found using Title or UPC
        DB.AddAvgDataBase({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found 0 Items", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price,'SearchedItems':[]})
        # db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found 0 Items", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price,'SearchedItems':[]})
        DB.AddErrorsDataBase({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found 0 Items", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price, 'SearchKeywords':ErrorAppendSearchKeywords, "EndTime": EndTime,"ImageURL" : ImageURL})
        # dbErrors.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found 0 Items", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price, 'SearchKeywords':ErrorAppendSearchKeywords, "EndTime": EndTime,"ImageURL" : ImageURL})
        return -1,CallText,[]  # Failure, No Items Found

    if(Prices == []):
        DB.AddAvgDataBase({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found Items but None Sold", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price,'SearchedItems':[]})
        # db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found Items but None Sold", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price,'SearchedItems':[]})
        DB.AddErrorsDataBase({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found Items but None Sold", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price, 'SearchKeywords':ErrorAppendSearchKeywords, "EndTime": EndTime,"ImageURL" : ImageURL})
        # dbErrors.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found Items but None Sold", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price, 'SearchKeywords':ErrorAppendSearchKeywords, "EndTime": EndTime,"ImageURL" : ImageURL})
        return -1,CallText,[]  # Failure, Items found but No Items Sold

    Average = statistics.mean(Prices)  # Calculate average price, put into data base
    DB.AddAvgDataBase({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': Average, "Time": time.time(), "ItemLink": ItemLink,'SearchedItems':SearchedItems, "ErrorRevision": CurrentErrorRevision})
    # db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': Average, "Time": time.time(), "ItemLink": ItemLink,'SearchedItems':SearchedItems, "ErrorRevision": CurrentErrorRevision})

    return Average,CallText,SearchedItems  # Success, New average price found


# Title to search take in a title and returns a simplified title
# URL is only used for adding item URL to log
# Success: Title Successfully Simplified : (str)
# Success: Multi Item Auction : "Multi Item Auction Found" + str(Matched Value)
def TitleToSearch (InputTitle,URL=None):
    MultiItemAuction = False
    Title = []
    Descriptors = []

    EditedTitle = InputTitle.encode('ascii', 'ignore').decode('ascii').lower() # Duplicate Title string

    for CharacterIndex in range(len(EditedTitle)):
        if (EditedTitle[CharacterIndex] in ",!@#$%^*_.?<>-/~`\:;" + '"'):
            EditedTitle = EditedTitle.replace(EditedTitle[CharacterIndex]," ")

    if('volume' in EditedTitle):
        EditedTitle = EditedTitle.replace("volume",'vol')

    # print(EditedTitle)

    # Chars to remove everything between
    for Brackets in [["(",")"],["[","]"],["{","}"]]:
        SearchToIndex = 0
        for i in range(min(EditedTitle.count(Brackets[0]),EditedTitle.count(Brackets[1]))):
            if Brackets[0] in EditedTitle[SearchToIndex:len(EditedTitle)] and Brackets[1] in EditedTitle[SearchToIndex:len(EditedTitle)]:
                StartIndex = EditedTitle[SearchToIndex:len(EditedTitle)].index(Brackets[0]) + SearchToIndex
                EndIndex = EditedTitle[SearchToIndex:len(EditedTitle)].index(Brackets[1]) + SearchToIndex
                SearchToIndex = EndIndex+1

                if(" " in EditedTitle[StartIndex:EndIndex] or EditedTitle[StartIndex+1:EndIndex-1].isdigit() or EditedTitle[StartIndex+1:EndIndex].lower() in ['dvd','bluray','blu-ray','new','used']):

                    Descriptors.append(EditedTitle[StartIndex:EndIndex+1])
                    Descriptors.append(EditedTitle[EndIndex + 1: len(EditedTitle)])

                    # print(Descriptors)

                    EditedTitle = EditedTitle[0:StartIndex]
                    break
        if Brackets[0] in EditedTitle and not Brackets[1] in EditedTitle:
            StartIndex = EditedTitle.index(Brackets[0])
            Descriptors.append(EditedTitle[StartIndex:len(EditedTitle)])
            EditedTitle = EditedTitle[0:StartIndex-1]

    # print(EditedTitle)
    # print(Descriptors)

    # Keys to replace
    for Replace in [['&','and'],['blue','blu']]:
        if(Replace[0] in EditedTitle):
            EditedTitle=EditedTitle.replace(Replace[0],Replace[1])

    #Multi Item Keys
    MultiItemKeywords = [['sets'], ['vol', '#', 'and', 'vol', '#'], ['#', 'and', '#'],
                         ['collection', '#', '#'], ['set', 'of', '#'], ['seasons', '#', '#'],['vol','#','#'],['vol','#','#','#'],['vol','#','#','#','#'],['vol','#','#','#','#','#'],['vol','#','#','#','#','#','#'],['vol','#','#','#','#','#','#','#'],
                         ['seasons', '#', 'and', '#'], ['seasons'], ['bundle'], ['films'],['volumes'],['manga','+','anime'],
                         ['anime','+','manga'], ['disc','#','disc','#'],[' + '],['multiple'],['titles'],['starter','set'],['lot','of','#'],
                         ['lot','of','two'],['lot','of','three'],['lot','of','four']]#Anime, The Empire Of Corpses Feature Film Blu-Ray DVD & Digital HD TVMA Unopened
    for Keyword in MultiItemKeywords:
        EditedTitleSearch = [("#" if float(a) < 1500 else a) if a.isdigit() else a for a in EditedTitle.split(" ")]
        RemovalCount = 0
        for i in range(len(EditedTitleSearch)):
            if EditedTitleSearch[i - RemovalCount] == "":
                EditedTitleSearch.pop(i - RemovalCount)
                RemovalCount = RemovalCount + 1
        for SearchSetIndex in range(len(EditedTitleSearch) - len(Keyword) + 1):
            # print(str(Keyword) + "  |  " + str(EditedTitleSearch[SearchSetIndex:SearchSetIndex+len(Keyword)]))
            if Keyword == EditedTitleSearch[SearchSetIndex:SearchSetIndex+len(Keyword)]:
                # print(str(Keyword) + "  |  " + str([("#" if float(a) < 1500 else a) if a.isdigit() else a for a in EditedTitle.split(" ")]))
                return "Multi Item Auction Found " + str(" ".join(Keyword))

    EditedTitle = EditedTitle.split(" ")

    RemovalCount = 0
    for i in range(len(EditedTitle)):
        if EditedTitle[i - RemovalCount] == "":
            EditedTitle.pop(i - RemovalCount)
            RemovalCount = RemovalCount + 1

    # print(EditedTitle)

    # Keys to remove in general
    DescriptiveWords = [['part','#'],['ovas','and','movie'],['anime','and','ova'],["limited","edition",'special','cd'],["limited","edition"],['dvd','collection'],['blu','ray','and','dvd'],['bluray','and','dvd'],['dvd','and','blu','ray'],['-vol','#','dvd','set'],['dvd','and','bluray'],['-vol','#','dvd','box','set'],
                        ['first','season','#'],['season','#'],['complete','#','dvd','series'],["collector's",'box'],['complete','dvd','set'],['dvd','set'],['bonus','dvd'],['dvd','feature'],['-vol','#','dvd','set'],['-vol','#','dvd'],['dvd'],["dub",'and','sub'],['sub','and','dub'],['dub'],['sub'],['subs'],['subtitle'],['dubs'],
                        ['the','complete','series'],['series','one'],
                        ['complete','series','collection'],['complete','series','boxset'],['complete','series'],['complete','set'],
                        ['sentai','filmworks'],["english"],["widescreen","edition"],['classic'],['like','new'],['used'],["brand","new"],["new"],["sealed"],['dubbed'],
                        ['subbed'],["region","#"],['anime','legends'],['complete','anime','series'],['anime','series'],['anime','works'],['good','anime'],["anime"],['dual','movie'],["-the","movie"],["blu","ray","combo","pack","with","slipcover"],['on','#','blu','ray'],['on','#','bluray'],['on','bluray'],['on','blu','ray'],['bluray','set'],['blu','ray','set'],['-vol','#','blu','ray'],
                        ['blu','ray','collection'],['bluray','collection'],['blu','ray','w','slipcover'],['bluray','w','slipcover'],["bluray"],["blu","ray"],
                        ['#','disc','set'],["#",'disc'],["#",'discs'],['rene','laloux'],['combo','pack'],['with','slipcover'],['matt','groening'],['fox','animated','series'],['limited','box','set'],['box','set'],
                        ['boxed','set'],['the','complete','collection'],['the','complete'],['complete','collection'],['sd'],['comp'],['feature','film'],['no','digital','code'],['digital','code'],['digital'],['ultra','hd'],['hd'],['tvma'],['unopened'],
                        ['funimation','release'],['funimation'],['oop'],['sentai','filmwork'],['out','of','print'],['episodes','#','#'],['#','episodes'],['usa'],['mint'],['r1'],['official'],['america'],['slipcover'],['bandai','entertainment'],['bandai'],['honneamise'],
                        ['japan','version'],['japan'],['f'],['s'],['subtitles'],['premium','edition'],['studio','ghibli'],['excellent'],['discotek'],['#','eps'],['series','complete'],['vhs'],['b'],['u'],['available'],['hk'],
                        ['in','shrink','wrap'],['complete','season'],['japanese','version'],['japanese'],['full','length'],['nickelodeon'],['special','edition'],['complete'],['box'],['geneon'],['kids'],['family'],['adv','films'],['adv'],['sentai'],['metal','tin'],['madman'],
                        ['plus','insert'],['only','disc'],['disc','only'],['3d'],['uhd'],['4k'],['best','buy','exclusive'],['very','nice'],['wide','screen'],['anchor','bay'],['rare'],['horror'],['free','shipping'],['perfect','collection'],
                        ['essential','collection','#'],['essential','collection'],['cartoon'],['pioneer'],['le'],
                        ['dts'],['orig'],['vg+'],['#>1500'],['e1','#'],['#','bd','disk'],['tv','series'],['tv'],['import'],['with','nendoroids','and','extras'],['with','dendoroids'],['with','extras'],['premium',"collector's",'edition'],['original','series'],
                        ['dream','works' ,"animation's"],['dreamworks','animation'],['-the','animation'],['juni','nishimura'],['with','all','promo','cells'],['korea'],['full','slip','keep','case'],['disney',"-animation","-collection"],['aniv','edition'],['anniversary','edition'],['anniv','edition'],
                        ['sci','fi'],['fantasy'],['drama'],['thriller'],['clamp'],["dvd's",'#','#','#'],["dvd's",'#','#'],["dvd's",'#'],["#","#"],['with'],['ova'],['never','opened'],['no','scraches'],['blu'],['rated','pg'],['rated','g'],['rated','r'],['rated'],['vintage'],['great','story'],['on'],['by'],['aardman'],['video'],['eng'],['lot'],['extras'],
                        ['ad','vision'],['collectible']]

    for Word in DescriptiveWords:
        for EditedTitleIndex in range(len(EditedTitle)-len(Word)+1):
            ComparisonWord = [("#" if int(a) < 1500 else "#>1500") if a.isdigit() else a for a in EditedTitle[EditedTitleIndex:EditedTitleIndex+len(Word)]]

            # print(str(Word) + "  |  " + str(ComparisonWord))

            WordC = [ComparisonWord[Word.index(a)] if "-" in a and a.replace("-","") not in ComparisonWord else a for a in Word]

            # print(str(WordC) + "  |  " + str(ComparisonWord))

            if(ComparisonWord == WordC):
                # print("hi")
                Descriptors.append(" ".join(EditedTitle[EditedTitleIndex:EditedTitleIndex+len(WordC)]))
                for DescriptWordIndex in range(len(ComparisonWord)):
                    # print(DescriptWordIndex)

                    if("-" not in Word[DescriptWordIndex]):
                        EditedTitle[EditedTitleIndex+DescriptWordIndex] = ""
        RemovalCount = 0
        for i in range(len(EditedTitle)):
            if EditedTitle[i - RemovalCount] == "":
                EditedTitle.pop(i - RemovalCount)
                RemovalCount = RemovalCount + 1

    if('vol' in EditedTitle):
        Descriptors.append(" ".join(EditedTitle[EditedTitle.index('vol'):len(EditedTitle)]))
        EditedTitle = EditedTitle[0:EditedTitle.index('vol')]

    RemovalCount = 0
    for i in range(len(EditedTitle)):
        if EditedTitle[i-RemovalCount] == "":
            EditedTitle.pop(i-RemovalCount)
            RemovalCount = RemovalCount + 1



    DescriptorsStr = Descriptors
    DescriptorsStr = " ".join(DescriptorsStr).split(" ")
    CompleteFound = 0
    for WordSet in [['complete'],['complete','series'],['platinum','edition'],['complete','collection'],['limited','edition'],['the','complete','box','set'],['complete','box','set'],['box','set']]:
        Good = 0
        for Word in WordSet:
            # print(Word + "  |  " + str(DescriptorsStr))
            if(Word in DescriptorsStr):
                Good = Good + 1
        if(Good >= len(WordSet)):
            EditedTitle.append(" ".join(WordSet))
            CompleteFound = 1
            break

    if(CompleteFound == 0):
        for WordFollowedByNumber in ['season','vol']:
            for Descript in Descriptors:
                # print(Descriptors)
                Item = Descript.split(" ")
                if(WordFollowedByNumber in Item and len(Item) > Item.index(WordFollowedByNumber)+1 and Item[Item.index(WordFollowedByNumber)+1].isdigit()):
                    EditedTitle.append(" ".join([Item[Item.index(WordFollowedByNumber)], Item[Item.index(WordFollowedByNumber)+1]]))

    # if('Hataraki Man complete collection bluray, 11 SD anime episodes on 1 blu ray NEW!!' in InputTitle):
    #     quit()
    for DiscTypeCheck in Descriptors:
        if('blu' in DiscTypeCheck and 'ray' in DiscTypeCheck):
            EditedTitle.append('bluray')
            break
        elif('dvd' in DiscTypeCheck):
            EditedTitle.append('dvd')
            break



    return " ".join(EditedTitle)
