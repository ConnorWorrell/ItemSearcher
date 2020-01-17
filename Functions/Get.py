import json
import requests
from tinydb import TinyDB, Query
import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import re
import Logs
import Ebay
import statistics

def UPC(ItemLink,UPCDataBase):
    Retries = 5
    SleepTime = 1


    ItemLink = ItemLink.split('?')[0]

    #db = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToUPC")
    db = UPCDataBase
    User = Query()

    Search = db.search(User.Link == ItemLink)
    if(Search != []):
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Cache: " + str(Search[0]['UPC']))
        return Search[0]['UPC']

    page = None

    for RetryNumber in range(Retries):
        try:
            page = requests.get(ItemLink)
        except:
            print("Connection Error, Retrying in " + str(SleepTime) + " seconds")
            time.sleep(SleepTime)  # wait before trying to fetch the data again
            SleepTime *= 2  # Implement your backoff algorithm here i.e. exponential backoff

    if(page == None):
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Error: Unable to resolve connection error after 5 attempts")
        return None

    soup = BeautifulSoup(page.text, 'html.parser')

    UPC_Find = soup.find(itemprop="gtin13")

    if (UPC_Find == None):
        UPC = -1
        db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: No UPC")
        return UPC

    UPC = UPC_Find.contents[0]
    if (UPC.isdigit() == False):
        UPC = -1
        db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})
        Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: No UPC")
        return UPC

    db.insert({'Link': ItemLink,'UPC': UPC, "Time": time.time()})

    Logs.Write("Get UPC From Item Link: " + ItemLink + " Returned: " + str(UPC))
    return UPC



def Shipping(ItemLink,driver,ShippingDataBase,WebDriverPath):
    WaitTimeBetweenButtons = .1
    zipCode = '80513'
    Retries = 5
    TimeoutTime = .5

    ItemLink = ItemLink.split('?')[0]

    #db = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToShipping")
    db = ShippingDataBase
    User = Query()

    Logs.Write("Starting Getting Shipping for " + ItemLink)

    Search = db.search(User.Link == ItemLink)
    if (Search != []):
        Logs.Write("Get Shipping From Item Link: " + ItemLink + " Cache: " + str(Search[0]['Shipping']))
        return Search[0]['Shipping'],driver

    #WebDriverPath = os.path.dirname(os.path.dirname(__file__)) + '/Drivers/chromedriver.exe'
    #driver = webdriver.Chrome(executable_path=WebDriverPath)

    time.sleep(
        random.uniform(1, 2) ** 2)

    for i in range(Retries):

        TimeoutTime = TimeoutTime * 2
        try: #Loading page, restarting driver if its closed
            driver.get(ItemLink)
        except:
            driver = webdriver.Chrome(executable_path=WebDriverPath)

        time.sleep(
            random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        try: #Check for item having ended way 1
            MissingListing1 = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "w3" + '"]/div/div/div/div/span/span'))).text
            if ("The listing you're looking for has ended." in MissingListing1):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item Auction Ended")
                db.insert(
                    {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1,driver
        except: #Passes check
            pass

        try: #Check for item having ended way 2
            MissingListing2 = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "mainContent-w0-w0-0" + '"]/div/div/span'))).text
            if("The listing you're looking for has ended." in MissingListing2):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item Auction Ended")
                db.insert(
                    {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1, driver
        except: #Passes Check
            pass

        try: #Check shipping to usa
            ShippingText = WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="' + "vi-acc-shpsToLbl-cnt" + '"]/span'))).text
            if('Worldwide' not in ShippingText and 'United States' not in ShippingText):
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Item does not ship to US")
                db.insert(
                    {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1, driver
        except:
            continue

        try: #Click shipping and payments button
            WebDriverWait(driver, TimeoutTime).until(
                EC.element_to_be_clickable((By.ID, "viTabs_1"))).click()
        except:
            continue
        time.sleep(
             random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        try: # check if seller specified shipping
            text = str(WebDriverWait(driver, TimeoutTime).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="' + "shCost-err" + '"]'))).text)
            if "seller has not specified shipping options" in text:
                Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Unspecified Shipping")
                db.insert(
                    {'Link': ItemLink, 'Shipping': -1, 'Raw': -1, "Time": time.time()})
                return -1, driver
        except:
            pass

        #Type zipcode into zipcode box
        for i in range(len(zipCode)):
            try:
                WebDriverWait(driver, TimeoutTime).until(
                    EC.element_to_be_clickable((By.ID, "shZipCode"))).send_keys(zipCode[i])
            except:
                continue
            time.sleep(
                random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2))

        try: #Click submit button for zip code
            WebDriverWait(driver, TimeoutTime).until(EC.element_to_be_clickable((By.ID, "shGetRates"))).click()
        except:
            continue
        time.sleep(
            random.uniform(WaitTimeBetweenButtons, WaitTimeBetweenButtons * 2) ** 2)

        try: #Read pricing data
            ShippingInfoRaw = str(WebDriverWait(driver, TimeoutTime).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="' + "shippingSection" + '"]/table/tbody/tr/td'))).text)
        except:
            continue
        if ('Free shipping' in ShippingInfoRaw):
            Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Free Shipping")
            db.insert({'Link': ItemLink, 'Shipping': 0, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return 0,driver
        if ('US' not in ShippingInfoRaw[0:5]):
            Logs.Write("Get Shipping From Item Link: " + ItemLink + " Returned: Shipping Price In Forien Currency: " + str(ShippingInfoRaw))
            db.insert({'Link': ItemLink, 'Shipping': -1, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return -1,driver

        OutputPrice = re.findall("\d+\.\d+", str(ShippingInfoRaw))

        if (OutputPrice != []):
            OutputShippingPrice = float(OutputPrice[0])
            Logs.Write(
                "Get Shipping From Item Link: " + ItemLink + " Returned: " + str(
                    OutputShippingPrice))
            db.insert({'Link': ItemLink, 'Shipping': OutputShippingPrice, 'Raw': ShippingInfoRaw, "Time": time.time()})
            return OutputShippingPrice,driver

    db.insert({'Link': ItemLink, 'Shipping': -1, 'Raw': None, "Time": time.time()})
    return -1,driver

#print(Shipping('https://www.ebay.com/itm/Mounted-Large-Brass-American-Eagle-Almost-6-pounds-18-inches-high-Unique-/254444583109',None))

def AvgPrice(ItemLink,Title,OutOfCalls,Price,ErrorAppendSearchKeywords,EndTime,AVGPriceDB,ErrorsDB,UPCDataBase):
    CurrentErrorRevision = 4
    Recalling = None

    #db = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToAvgPrice")
    #dbErrors = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors")

    db = AVGPriceDB
    dbErrors = ErrorsDB

    User = Query()

    if(ItemLink == None):
        TitleSearch = Title
        UPCCode = -1
    else:
        UPCCode = UPC(ItemLink,UPCDataBase)
        TitleSearch = TitleToSearch(Title,URL=ItemLink)
    #print(UPCCode)



    if (UPCCode != -1):
        CallText = UPCCode
        #print('hi')
    else:
        CallText = TitleSearch

    if(TitleSearch == True):
        print('hi7')
        return -1,"Multi Item Auction Found",[]

    Search = db.search(User.CallText == CallText)
    # print(Search)
    # Search1 = db.search(User.Link == CallText)
    # print(Search1)



    if (Search != []):  # If UPC Cached grab from database

        print(Search[0])

        RecallTime = float(60 * 60 * 24 * 7)
        #print(str(float(Search[0]["Time"])) + " " + str(time.time()) + " " + (str(Search[0])))

        try:
            Search[0]["ErrorRevision"]
            Search[0]['SearchedItems']
        except:
            Recalling = 1
            print("Missing Revision")
            try:
                db.remove(User.CallText == CallText)
            except:
                db.remove(User.Link == CallText)

        if (Recalling == None and float(Search[0]["Time"]) + RecallTime < time.time() and Search[0]['AvgPrice'] > 0):
            Logs.Write("Recalling AVG Price for Item with previous avg price: " + str(str(CallText)))
            #print("Recalling1: " + str(Search[0]))
            Recalling = 1
        elif (Recalling == None and float(Search[0]["Time"]) + RecallTime < time.time() and Search[0]['AvgPrice'] < 0):
            Logs.Write("Recalling AVG Price for Item without previous avg price: " + str(str(CallText)))
            #print("Recalling2: " + str(Search[0]))
            Recalling = 0
        elif(Recalling == None and Search[0]["ErrorRevision"] == CurrentErrorRevision):
            Logs.Write("Get AVG Price from UPC: " + str(CallText) + " Cache: " + str(Search[0]['AvgPrice']))
            print('hi0')
            print(CallText,Search[0]['SearchedItems'])
            return Search[0]['AvgPrice'], CallText,Search[0]['SearchedItems']


        #if(Search[0]['AvgPrice'] < 0 ):

        if(len(Search) > 1):
            print("Search is greater than 1, this is a problem: " + str(Search))
            print([ItemLink,Title,OutOfCalls,Price,ErrorAppendSearchKeywords,EndTime])

            for i in range(len(Search)):
                try:
                    db.remove(User.CallText == CallText)
                    print("Removed Extra")
                except:
                    db.remove(User.Link == CallText)
                    print("Removed Extra")

        try:
            if(Recalling == None and Search[0]["ErrorRevision"] != CurrentErrorRevision):
                print("Removed")
                # for i in range(1000):
                # try:
                #print(CallText)
                db.remove(User.CallText == CallText)
                # except:
                #     break
            elif(Recalling == None and Search[0]['avgPrice'] < 0):
                ErrorCode = Search[0]
                ErrorCode['SearchKeywords'] = ErrorAppendSearchKeywords
                ErrorCode["EndTime"] = EndTime
                ErrorCode["ItemLink"] = ItemLink
                dbErrors.insert(ErrorCode)
                print('hi1')
                return Search[0]['AvgPrice'],CallText,Search[0]['SearchedItems']
        except:
            if (Recalling == None and Search[0]["ErrorRevision"] != CurrentErrorRevision):
                print("Removed2")
                db.remove(User.Link == CallText)


    if(OutOfCalls == 1):
        print("Repeat Out Of Calls")
        return -2,None,[]

    Prices = []
    SearchedItems = []

    Count = 0
    Count1 = 0
    Count2 = 0

    if(CallText == TitleSearch):
        Responce = Ebay.Call(CallText,0,1,10000,0,0)
        try:
            Count = int(Responce['findCompletedItemsResponse'][0]['searchResult'][0]['@count'])
        except:
            print(CallText)
            if ('Keyword or category ID are required.' in str(Responce)):
                print('Keyword or category ID are required')
                db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(),
                           "Error": "Keyword or category ID are required", "ErrorRevision": CurrentErrorRevision,
                           "ItemLink": ItemLink, "Price": Price})
                print('hi2')
                return -1, None,[]

            print("Used All Calls" + str(Responce))
            return -2, None,[]
        for Index in range(Count):
            Item = Responce['findCompletedItemsResponse'][0]['searchResult'][0]['item'][Index]
            if (Item['sellingStatus'][0]['sellingState'][0] == 'EndedWithSales'):
                print(Item)
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
                print('Searched Items1' + str(SearchedItems))
    else:
        print("Calling both UPC and Title")
        Responce1 = Ebay.Call(UPCCode,0,1,10000,0,0)
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


        if(Prices == []):
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

    #print([Count,Count1,Count2])
    print(Prices)

    if (Recalling == 1 and Prices != []):
        db.remove(User.CallText == CallText)
        print("Recalling: " + str(Search[0]))
    elif(Recalling == 1):
        print("Had Past price for item, but couldn't find new price: " + str(Search[0]))

        try:
            Search[0]['SearchedItems']
            hi=0
        except:
            hi=1
            db.remove(User.CallText == CallText)
        if(hi == 0):
            NewCall = Search[0]
            NewCall["Time"] = time.time()
            db.remove(User.CallText == CallText)
            db.insert(NewCall)
            print('hi3')

            return Search[0]['AvgPrice'],CallText,Search[0]['SearchedItems']

    elif(Recalling == 0):
        db.remove(User.CallText == CallText)

    if Count == 0 and (Count1 == 0 and Count2 == 0):
        print('hi6')
        db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found 0 Items", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price,'SearchedItems':[]})
        dbErrors.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found 0 Items", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price, 'SearchKeywords':ErrorAppendSearchKeywords, "EndTime": EndTime})
        #print("Found nothing For1: " + Title)
        print('hi4')
        return -1,CallText,[]

    if(Prices == []):
        db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found Items but None Sold", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price,'SearchedItems':[]})
        dbErrors.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': -1, "Time": time.time(), "Error": "Found Items but None Sold", "ErrorRevision": CurrentErrorRevision, "ItemLink": ItemLink, "Price":Price, 'SearchKeywords':ErrorAppendSearchKeywords, "EndTime": EndTime})
        #print("Found nothing For2: " + Title)
        print('hi5')
        return -1,CallText,[]

    print('Searched Items' + str(SearchedItems))

    Average = statistics.mean(Prices)
    db.insert({'CallText': CallText, "ItemTitle": Title, 'AvgPrice': Average, "Time": time.time(), "ItemLink": ItemLink,'SearchedItems':SearchedItems, "ErrorRevision": CurrentErrorRevision})

    print(str(Average) + " Found For: " + Title)

    print("hi")
    return Average,CallText,SearchedItems

    #db.insert({'SearchTitle': UPCCode,"AvgPrice": AveragePrice,"Time":time.time()})
    #return AveragePrice




#AvgPrice('https://www.ebay.com/itm/Love-and-Medabots-volume-8-DVD-OOP-RARE-ANIME-SEALED-NO-SHRINK-WRAP-CARTOON-/202842752417','hi')

def TitleToSearch (Title,URL=None):

    MultiItemAuction = False
    OrigionalTitle = Title

    EditedTitle = Title[0:len(Title)]

    EditedTitle = EditedTitle.replace("("," ").replace(")"," ")

    if('US ' in EditedTitle or ' US' in EditedTitle):
        EditedTitle = EditedTitle.replace("US",'')

    EditedTitle = EditedTitle.lower()

    for IndiscrimantlyRemove in ["18+"]:
        EditedTitle = EditedTitle.replace(IndiscrimantlyRemove,"")

    for i in Title:
        if i not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 '":
            EditedTitle = EditedTitle.replace(i," ")

    if('blu ray' in EditedTitle):
        EditedTitle = EditedTitle.replace("blu ray","bluray")

    if 'feature film' in EditedTitle:
        EditedTitle = EditedTitle.replace('feature film','')

    if('episode' in EditedTitle and 'episode ' not in EditedTitle and 'episodes' not in EditedTitle):
        EditedTitle = EditedTitle.replace('episode','episode ')

    for i in ['near new','brand new']:
        if(i in EditedTitle):
            EditedTitle = EditedTitle.replace(i,'')

    if('on dvd' in EditedTitle):
        EditedTitle = EditedTitle.replace('on dvd', 'dvd')

    EditedTitle = EditedTitle.split(" ")

    for i in range(100):
        try:
            EditedTitle.remove("")
        except:
            break

    EditedTitle = [a.lower() for a in EditedTitle]

    for RemoveWordAlways in ['anime','premium','limited','edition','cartoon','japanese','hotshots']: #questioning edition
        if(RemoveWordAlways in EditedTitle):
            EditedTitle.remove(RemoveWordAlways)

    if EditedTitle[0].isdigit():
        EditedTitle.append(EditedTitle[0])
        EditedTitle = EditedTitle[1:len(EditedTitle)]

    for i in range(len(EditedTitle)):
        if EditedTitle[0] in ['anime','premium','limited','edition','cartoon','japanese','hotshots', 'vol', 'used', 'cd', 'collection','dvd']:
            TempStorage = EditedTitle[0]
            EditedTitle = EditedTitle[1:len(EditedTitle)]
            EditedTitle.append(TempStorage)
        else:
            break

    for RemoveFirstWord in ['new','anime']:
        if(RemoveFirstWord in EditedTitle and EditedTitle.index(RemoveFirstWord) == 0):
            EditedTitle = EditedTitle[1:len(EditedTitle)]
            break

    for RemoveAfterWordCheckNumber in ['collection','set','complete','bluray','seasons','season','volume','vol','vol.','part','parts','episode','dvd']:
        if(RemoveAfterWordCheckNumber in EditedTitle and EditedTitle.index(RemoveAfterWordCheckNumber) < len(EditedTitle)):
            try:
                if(EditedTitle.index(RemoveAfterWordCheckNumber)+1 < len(EditedTitle) and EditedTitle[EditedTitle.index(RemoveAfterWordCheckNumber)+1] in '1234567891011121314151617181920onetwothreefourfivesixseveneightnineteneleventwelve1st2nd3rd4th5th6th7th8th9th10th010203040506070809IIIVIII'):

                    if (EditedTitle.index(RemoveAfterWordCheckNumber) + 2 < len(EditedTitle) and EditedTitle[
                        EditedTitle.index(
                            RemoveAfterWordCheckNumber) + 2] in ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20',','
                                                        'one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','01','02','03','04','05','06','07','08','09','I','II','III','IV','V','VI','VII','VIII','IX','X','w']):
                        MultiItemAuction = True
                    EditedTitle = EditedTitle[0:EditedTitle.index(RemoveAfterWordCheckNumber) + 2]
                else:
                    EditedTitle = EditedTitle[0:EditedTitle.index(RemoveAfterWordCheckNumber)+1]
            except:
                print("Failed 123: " + str(EditedTitle))
                EditedTitle = EditedTitle[0:EditedTitle.index(RemoveAfterWordCheckNumber)]

    for RemoveFirstWord in ['essentials', 'new',"blu-ray",'blu-ray/dvd','bluray/dvd']:
        if (RemoveFirstWord in EditedTitle and EditedTitle.index(RemoveFirstWord) < len(
                EditedTitle)):
            try:
                    EditedTitle = EditedTitle[0:EditedTitle.index(RemoveFirstWord) + 1]
            except:
                # print("Failed 123: " + str(EditedTitle))
                EditedTitle = EditedTitle[0:EditedTitle.index(RemoveFirstWord)]

    for RemoveLastWord in ['the']:
        if(RemoveLastWord == EditedTitle[len(EditedTitle)-1]):
            EditedTitle.pop(len(EditedTitle)-1)

    for Numbers in EditedTitle:
        if Numbers.isdigit() == True and int(Numbers) > 1500:
            EditedTitle = EditedTitle[0:EditedTitle.index(Numbers) + 1]
            break

    try:
        for discVariant in ['disc','discs']:
            if discVariant in EditedTitle and EditedTitle[EditedTitle.index(discVariant)-1].isdigit():
                Number = EditedTitle[EditedTitle.index(discVariant)-1]
                EditedTitle.remove(Number)
                EditedTitle.remove(discVariant)
    except:
        print("Write disc is first word in search title, fix this ebay.get()")
        pass

    for discVariantNoRemovedisc in ['dvd','episodes']:
        if discVariantNoRemovedisc in EditedTitle and EditedTitle[EditedTitle.index(discVariantNoRemovedisc) - 1].isdigit():
            Number = EditedTitle[EditedTitle.index(discVariantNoRemovedisc) - 1]
            EditedTitle.remove(Number)

    if 'disc' in EditedTitle:
        EditedTitle.remove('disc')

    for LargeNumberCheck in EditedTitle:
        if LargeNumberCheck.isdigit() and int(LargeNumberCheck) > 1000:
            EditedTitle.remove(LargeNumberCheck)

    EditedTitle = " ".join(EditedTitle)

    if 'box set' in EditedTitle:
        EditedTitle = EditedTitle.replace('box set','box set boxset')

    #print(EditedTitle + "                       Origional: " + OrigionalTitle)

    if(MultiItemAuction == False):
        Logs.Write("Title From Text: " + str(Title) + " | " + str(EditedTitle))
        return EditedTitle
    else:
        if(URL == None):
            URL = ""
        print("Multi Item Auction Found: " + str(Title) + " | " + str(EditedTitle) + " " + str(URL))
        Logs.Write("Title From Text Found MultiItemAuction: " + str(Title) + " | " + str(EditedTitle) + " " + str(URL))
        return True #EditedTitle

#
#WebDriverPath = os.path.dirname(os.path.dirname(__file__)) + '/Drivers/chromedriver.exe'
#drivers = webdriver.Chrome(executable_path=WebDriverPath)
#
#
#price1,drivers=Shipping('https://www.ebay.com/itm/Duke-Ellington-Memories-of-Duke-VHS-Mexican-Suite-/160539819435?_trksid=p5731.m3795',drivers)
#print(price1)
# price2,drivers = Shipping('https://www.ebay.com/itm/Disney-A-Kid-in-King-Arthurs-Court-VHS-Clamshell-EUC-/160562251316?_trksid=p5731.m3795',drivers)
#
#
# print(str(price1) + " " + str(price2))

# print(TitleToSearch('cartoon haibane renmei 4 dvd box set'))