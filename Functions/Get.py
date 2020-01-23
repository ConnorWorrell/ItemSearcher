import requests
from tinydb import Query
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
def UPC(ItemLink,UPCDataBase):
    Retries = 5  # Number of times that getting the UPC will be attempted before giving up
    SleepTime = 1  # Time in seconds to delay between failed attempts (doubling each attempt)

    ItemLink = ItemLink.split('?')[0]  # Remove un-needed information from URL link

    db = UPCDataBase
    User = Query()

    Search = db.search(User.Link == ItemLink)  # Search for URL in database
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
        db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: No UPC")
        return UPC  # Failure to find UPC

    UPC = UPC_Find.contents[0]
    if (UPC.isdigit() == False): # If page found UPC code but it dosen't match up with expected codes
        UPC = -1 # Failure to get UPC Code
        db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: No UPC")
        return UPC  # Failure to find UPC

    # UPC is found and it is in expected format
    # Place UPC into database
    db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})

    Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: " + str(UPC))
    return UPC  # Success finding UPC


# Shipping gets shipping price from a database using the URL and if it's not in the database then it attempts to find
# it online
# driver is the browser driver that is being used and it is provided and returned by the function so that it is not
# necessary to restart the browser every time
# Success: Free Shipping : 0, Found Shipping Price: (float)
# Failure: Generic Error : -1, check Logs for more information
def Shipping(ItemLink,driver,ShippingDataBase,WebDriverPath):
    WaitTimeBetweenButtons = .1 # Wait time between character inserts when typing in zip code
    global ReceivingZipCode
    zipCode = ReceivingZipCode # Zip code of receiving location for calculating shipping
    Retries = 5  # Number of times that scraping will be attempted before giving up
    TimeoutTime = .5  # Time given to web driver to load before interacting with page

    ItemLink = ItemLink.split('?')[0]  # Remove un-necessary information from URL

    db = ShippingDataBase
    User = Query()

    Logs.Write("Starting Getting Shipping for " + ItemLink)

    Search = db.search(User.Link == ItemLink)  # Look in database for shipping information
    if (Search != []):  # If shipping information is found in database
        Logs.Write("Get Shipping From Item Link: " + ItemLink + " Cache: " + str(Search[0]['Shipping']))
        return Search[0]['Shipping'],driver # Success, found in database

    for i in range(Retries):  # Number of attempts

        TimeoutTime = TimeoutTime * 2  # If failed to scrape double the timeout
        try:  # Loading page, restarting driver if its closed
            driver.get(ItemLink)
        except:
            driver = webdriver.Chrome(executable_path=WebDriverPath)
            driver.get(ItemLink)

        time.sleep(  # Wait for page to load before interacting
            random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        try:  # Check for item having ended way 1
            MissingListing1 = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "w3" + '"]/div/div/div/div/span/span'))).text
            if ("The listing you're looking for has ended." in MissingListing1):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item Auction Ended")
                db.insert(
                    {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1,driver  # Failure, item listing has ended
        except:  # Passes check
            pass

        try:  # Check for item having ended way 2
            MissingListing2 = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "mainContent-w0-w0-0" + '"]/div/div/span'))).text
            if("The listing you're looking for has ended." in MissingListing2):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item Auction Ended")
                db.insert(
                    {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1, driver  # Failure, item listing has ended
        except:  # Passes Check
            pass

        try:  # Check shipping to usa
            ShippingText = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "vi-acc-shpsToLbl-cnt" + '"]/span'))).text
            if('Worldwide' not in ShippingText and 'United States' not in ShippingText):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item does not ship to US")
                db.insert(
                    {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
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
                db.insert(
                    {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1, driver  # Seller did not pick a shipping option
            # Seller picked a shipping option
        except:
            pass  # Could not locate element, seller probably specified shipping

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
            random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        try:  # Read pricing data
            ShippingInfoRaw = str(WebDriverWait(driver, TimeoutTime).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="' + "shippingSection" + '"]/table/tbody/tr/td'))).text)
        except:  # Could not find pricing data reloading page
            continue

        if ('Free shipping' in ShippingInfoRaw):  # Check for free shipping
            Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Free Shipping")
            db.insert({'Link': ItemLink, 'Shipping': 0, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return 0,driver  # Success, item has free shipping

        if ('US' not in ShippingInfoRaw[0:5]):  # Check for currency that is not USD
            Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Shipping Price In Forien Currency: " + str(ShippingInfoRaw))
            db.insert({'Link': ItemLink, 'Shipping': -1, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return -1,driver  # Failure, item does not use us currency

        OutputPrice = re.findall("\d+\.\d+", str(ShippingInfoRaw))  # Match float string to text

        if (OutputPrice != []):  # If found string matching a price
            OutputShippingPrice = float(OutputPrice[0])
            Logs.Write(
                "Get Shipping From Item Link: " + ItemLink + " Returned: " + str(
                    OutputShippingPrice))
            db.insert({'Link': ItemLink, 'Shipping': OutputShippingPrice, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return OutputShippingPrice,driver  # Success, found shipping price

    db.insert({'Link': ItemLink, 'Shipping': -1, 'Raw': None, "Time": time.time()})
    return -1,driver  # Failed after number of attempts


# AvgPrice takes an ItemURL and returns an approximate average price from a database or from the web
# Note: 3 identical sections of code that could be condensed
# Success: (float), Found new avg price, Found cached avg price, Could not find new avg price but had old avg price
# Failure: Multi Item Auction Predicted : -1, Out Of Calls : -2, No items found : -1, No items sold : -1
def AvgPrice(ItemLink,Title,OutOfCalls,Price,ErrorAppendSearchKeywords,EndTime,AVGPriceDB,ErrorsDB,UPCDataBase):
    CurrentErrorRevision = 4 # Stored in database incase new things need to be added
    Recalling = None

    db = AVGPriceDB
    dbErrors = ErrorsDB

    User = Query()

    if(ItemLink == None):  # If no item link is given
        TitleSearch = Title  # Searching based on title
        UPCCode = -1
        CallText = TitleSearch
    else:  # Item link is given
        UPCCode = UPC(ItemLink,UPCDataBase)  # Grab UPC of item
        TitleSearch = TitleToSearch(Title,URL=ItemLink)  # Grab simplified title to search by
        CallText = TitleSearch

    if(TitleSearch == True):  # If TitleToSearch predicts the auction has multiple items in it
        return -1,"Multi Item Auction Found",[]  # Failure, avg price is inconsistent for multi item sales

    Search = db.search(User.CallText == CallText)  # Check if avg price is in database

    if (Search != []):  # If avg price Cached grab from database
        RecallTime = float(60 * 60 * 24 * 7)  # Time between when avg price is stored to next time it is updated

        try:  # Make sure that avg price has ErrorRevision and SearchedItems keywords
            Search[0]["ErrorRevision"]
            Search[0]['SearchedItems']
        except:  # if it does not then
            Recalling = 1  # Recall the avg price
            print("Missing Revision")
            try:
                db.remove(User.CallText == CallText)  # Remove the item from the database
            except:
                db.remove(User.Link == CallText)  # Remove the item from the database

        # Check if it should recalling AVG Price for Item with previous avg price
        if (Recalling == None and float(Search[0]["Time"]) + RecallTime < time.time() and Search[0]['AvgPrice'] > 0):
            Logs.Write("Recalling AVG Price for Item with previous avg price: " + str(str(CallText)))
            Recalling = 1

        # Check if it should recall avg price for item without previous avg price
        elif (Recalling == None and float(Search[0]["Time"]) + RecallTime < time.time() and Search[0]['AvgPrice'] < 0):
            Logs.Write("Recalling AVG Price for Item without previous avg price: " + str(str(CallText)))
            Recalling = 0

        # Check if error revision number is the correct number, if it is then the cached avg price is still valid
        elif(Recalling == None and Search[0]["ErrorRevision"] == CurrentErrorRevision):
            Logs.Write("Get AVG Price from UPC: " + str(CallText) + " Cache: " + str(Search[0]['AvgPrice']))
            return Search[0]['AvgPrice'], CallText,Search[0]['SearchedItems']  # Success, cached price

        if(len(Search) > 1):  # If multiple items are found, this mean a mistake occured and duplicate
                              # entries in the data base exist
            print("Search is greater than 1, this is a problem: " + str(Search))
            print([ItemLink,Title,OutOfCalls,Price,ErrorAppendSearchKeywords,EndTime])

            for i in range(len(Search)):  # Remove duplicate entries and recall
                try:
                    db.remove(User.CallText == CallText)
                    print("Removed Extra")
                except:
                    db.remove(User.Link == CallText)
                    print("Removed Extra")

        try:
            # If not recalling and error revision number is incorrect remove item from database
            if(Recalling == None and Search[0]["ErrorRevision"] != CurrentErrorRevision):
                print("Removed incorrect error revision number")
                db.remove(User.CallText == CallText)

            # If not recalling and cached avg price was -1 (Error or Unable to find price)
            elif(Recalling == None and Search[0]['avgPrice'] < 0):
                ErrorCode = Search[0]  # Mix item specific information into database information and return
                ErrorCode['SearchKeywords'] = ErrorAppendSearchKeywords
                ErrorCode["EndTime"] = EndTime
                ErrorCode["ItemLink"] = ItemLink
                dbErrors.insert(ErrorCode)
                return Search[0]['AvgPrice'],CallText,Search[0]['SearchedItems']  # Success, returning previous Failure
        except:  # If something failed with the databases then recall, remove item if it has the wrong error revision
            if (Recalling == None and Search[0]["ErrorRevision"] != CurrentErrorRevision):
                print("Removed2")
                db.remove(User.Link == CallText)


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
                db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(),
                           "Error": "Keyword or category ID are required", "ErrorRevision": CurrentErrorRevision,
                           "ItemLink": ItemLink, "Price": Price})
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
        db.remove(User.CallText == CallText)  # remove previous avg price
        print("Recalling: " + str(Search[0]))
    elif(Recalling == 1):  # If recalling item with previous avg price but no new avg price found
        print("Had Past price for item, but couldn't find new price: " + str(Search[0]))

        try:  # Make sure that previous search had Searched Items
            Search[0]['SearchedItems']
            SearchedItemsKeyErrorFailure=0
        except:  # If previous search did not have Searched items then remove it from the data base
            SearchedItemsKeyErrorFailure=1
            db.remove(User.CallText == CallText)
        if(SearchedItemsKeyErrorFailure == 0):  # If previous search had searched items then
            NewCall = Search[0]  # refresh search in database, wait another time period before searching again
            NewCall["Time"] = time.time()
            db.remove(User.CallText == CallText)
            db.insert(NewCall)

            return Search[0]['AvgPrice'],CallText,Search[0]['SearchedItems']  # Success, returned old avg price

    elif(Recalling == 0):  # If recalling item with no previous average price, then remove db entry
        db.remove(User.CallText == CallText)

    if Count == 0 and (Count1 == 0 and Count2 == 0):  # If no items were found using Title or UPC
        db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found 0 Items", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price,'SearchedItems':[]})
        dbErrors.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found 0 Items", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price, 'SearchKeywords':ErrorAppendSearchKeywords, "EndTime": EndTime})
        return -1,CallText,[]  # Failure, No Items Found

    if(Prices == []):
        db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found Items but None Sold", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price,'SearchedItems':[]})
        dbErrors.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found Items but None Sold", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price, 'SearchKeywords':ErrorAppendSearchKeywords, "EndTime": EndTime})
        return -1,CallText,[]  # Failure, Items found but No Items Sold

    Average = statistics.mean(Prices)  # Calculate average price, put into data base
    db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': Average, "Time": time.time(), "ItemLink": ItemLink,'SearchedItems':SearchedItems, "ErrorRevision": CurrentErrorRevision})

    return Average,CallText,SearchedItems  # Success, New average price found


# Title to search take in a title and returns a simplified title
# URL is only used for adding item URL to log
# Success: Title Successfully Simplified : (str)
# Success: Multi Item Auction : True
def TitleToSearch (Title,URL=None):

    MultiItemAuction = False

    EditedTitle = Title[0:len(Title)]  # Duplicate Title string

    EditedTitle = EditedTitle.replace("("," ").replace(")"," ")  # Replace () with spaces

    if('US ' in EditedTitle or ' US' in EditedTitle):  # Remove characters
        EditedTitle = EditedTitle.replace("US",'')

    EditedTitle = EditedTitle.lower()  # Set entire string to lower case

    for IndiscrimantlyRemove in ["18+"]:  # Remove no matter what
        EditedTitle = EditedTitle.replace(IndiscrimantlyRemove,"")

    for i in Title:  # replace all weird characters with spaces
        if i not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 '":
            EditedTitle = EditedTitle.replace(i," ")

    if('blu ray' in EditedTitle):  # replace string with other string
        EditedTitle = EditedTitle.replace("blu ray","bluray")

    if 'feature film' in EditedTitle:  # remove string
        EditedTitle = EditedTitle.replace('feature film','')

    # replace string ie: "episode10" -> "episode 10"
    if('episode' in EditedTitle and 'episode ' not in EditedTitle and 'episodes' not in EditedTitle):
        EditedTitle = EditedTitle.replace('episode','episode ')

    for i in ['near new','brand new']:  # remove string
        if(i in EditedTitle):
            EditedTitle = EditedTitle.replace(i,'')

    if('on dvd' in EditedTitle):  # replace string
        EditedTitle = EditedTitle.replace('on dvd', 'dvd')

    EditedTitle = EditedTitle.split(" ")  # turn into array of words

    for i in range(100):  # remove empty strings in array
        try:
            EditedTitle.remove("")
        except:
            break

    EditedTitle = [a.lower() for a in EditedTitle]  # make lowercase again???

    for RemoveWordAlways in ['anime','premium','limited','edition','cartoon','japanese','hotshots']: # remove words
        if(RemoveWordAlways in EditedTitle):
            EditedTitle.remove(RemoveWordAlways)

    if EditedTitle[0].isdigit():  # if first character is number move number to back
        EditedTitle.append(EditedTitle[0])
        EditedTitle = EditedTitle[1:len(EditedTitle)]

    for i in range(len(EditedTitle)):  # cycle words from the front to the back if they are in array, until word not in
                                       # array ends up as the first word
        if EditedTitle[0] in ['anime','premium','limited','edition','cartoon','japanese','hotshots', 'vol', 'used', 'cd', 'collection','dvd']:
            TempStorage = EditedTitle[0]
            EditedTitle = EditedTitle[1:len(EditedTitle)]
            EditedTitle.append(TempStorage)
        else:
            break

    for RemoveFirstWord in ['new','anime']:  # If words were at the beginning, remove them
        if(RemoveFirstWord in EditedTitle and EditedTitle.index(RemoveFirstWord) == 0):
            EditedTitle = EditedTitle[1:len(EditedTitle)]
            break

    # Remove words after a word in the array unless the word is followed by a number then remove everything after the number
    for RemoveAfterWordCheckNumber in ['collection','set','complete','bluray','seasons','season','volume','vol','vol.','part','parts','episode','dvd']:
        if(RemoveAfterWordCheckNumber in EditedTitle and EditedTitle.index(RemoveAfterWordCheckNumber) < len(EditedTitle)):
            # Word in array is also in Edited Title
            try:
                # If next word in Edited Title is followed by a number
                if(EditedTitle.index(RemoveAfterWordCheckNumber)+1 < len(EditedTitle) and EditedTitle[EditedTitle.index(RemoveAfterWordCheckNumber)+1] in '1234567891011121314151617181920onetwothreefourfivesixseveneightnineteneleventwelve1st2nd3rd4th5th6th7th8th9th10th010203040506070809IIIVIII'):

                    # If word 2 after in Edited Title is also a number then predict that the auction has multiple items
                    if (EditedTitle.index(RemoveAfterWordCheckNumber) + 2 < len(EditedTitle) and EditedTitle[
                        EditedTitle.index(
                            RemoveAfterWordCheckNumber) + 2] in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20',','
                                                        'one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','01','02','03','04','05','06','07','08','09','I','II','III','IV','V','VI','VII','VIII','IX','X','w']):
                        MultiItemAuction = True  # Set MultiItemAuction True
                    EditedTitle = EditedTitle[0:EditedTitle.index(RemoveAfterWordCheckNumber) + 2]  # chop Edited title down to size
                else:
                    EditedTitle = EditedTitle[0:EditedTitle.index(RemoveAfterWordCheckNumber)+1]  # chop Edited title down to size
            except:
                print("Failed 123: " + str(EditedTitle))
                EditedTitle = EditedTitle[0:EditedTitle.index(RemoveAfterWordCheckNumber)]

    # If word is in array then remove everything after it
    for RemoveWord in ['essentials', 'new',"blu-ray",'blu-ray/dvd','bluray/dvd']:
        if (RemoveWord in EditedTitle and EditedTitle.index(RemoveWord) < len(
                EditedTitle)):
            try:
                    EditedTitle = EditedTitle[0:EditedTitle.index(RemoveWord) + 1]
            except:
                EditedTitle = EditedTitle[0:EditedTitle.index(RemoveWord)]

    for RemoveLastWord in ['the']:  # if the last word in array is 'the' then remove it
        if(RemoveLastWord == EditedTitle[len(EditedTitle)-1]):
            EditedTitle.pop(len(EditedTitle)-1)

    for Numbers in EditedTitle:  # If numbers in edited array are large then remove everything after them
        if Numbers.isdigit() == True and int(Numbers) > 1500:
            EditedTitle = EditedTitle[0:EditedTitle.index(Numbers) + 1]
            break

    try:  # if array has #,'disc' in it remove both # and 'disc'
        for discVariant in ['disc','discs']:
            if discVariant in EditedTitle and EditedTitle[EditedTitle.index(discVariant)-1].isdigit():
                Number = EditedTitle[EditedTitle.index(discVariant)-1]
                EditedTitle.remove(Number)
                EditedTitle.remove(discVariant)
    except:
        print("Write disc is first word in search title, fix this ebay.get()")
        pass

    # if array has #, 'dvd' in it remove #
    for discVariantNoRemovedisc in ['dvd','episodes']:
        if discVariantNoRemovedisc in EditedTitle and EditedTitle[EditedTitle.index(discVariantNoRemovedisc) - 1].isdigit():
            Number = EditedTitle[EditedTitle.index(discVariantNoRemovedisc) - 1]
            EditedTitle.remove(Number)

    if 'disc' in EditedTitle:  # remove string
        EditedTitle.remove('disc')

    for LargeNumberCheck in EditedTitle:  # Remove numbers larger than 1000
        if LargeNumberCheck.isdigit() and int(LargeNumberCheck) > 1000:
            EditedTitle.remove(LargeNumberCheck)

    EditedTitle = " ".join(EditedTitle)  # Join array back together

    if 'box set' in EditedTitle:  # Replace string
        EditedTitle = EditedTitle.replace('box set','box set boxset')

    if(MultiItemAuction == False):
        Logs.Write("Title From Text: " + str(Title) + " | " + str(EditedTitle))
        return EditedTitle  # Success, Successfully Simplified Title

    else:  # Multi item auction Found
        if(URL == None):
            URL = ""
        print("Multi Item Auction Found: " + str(Title) + " | " + str(EditedTitle) + " " + str(URL))
        Logs.Write("Title From Text Found MultiItemAuction: " + str(Title) + " | " + str(EditedTitle) + " " + str(URL))
        return True  # Success, Multi Item Auction Predicted
