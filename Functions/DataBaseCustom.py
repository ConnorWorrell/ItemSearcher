import os
import json
import atexit

UPCDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToUPC"
ShippingDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToShipping"
AvgPriceDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToAvgPrice"
ErrorsDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errors"
DisplayDataDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/DisplayData.txt"
CallCountDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/CallCount"

UPCDataBase = {}
ShippingDataBase = {}
AvgPriceDataBase = {}
ErrorsDataBase = {}
DisplayDataDataBase = {}
CallCountDataBase = {}

DatabaseWritesBeforePush = 100  # Writes between saving files
DataBaseWrites = {}

# Sets up proper variables for use in database stuff
def Startup():
    global UPCDataBase, ShippingDataBase, AvgPriceDataBase, ErrorsDataBase, DisplayDataDataBase, CallCountDataBase,DataBaseWrites,InitialDataBaseSizes

    def Start(Path,DB):
        DataBaseWrites[Path] = 0  # Reset writes between saving files count
        if (os.path.exists(Path)):  # Check to see if database exists, if it does then load it
            with open(Path, 'r') as in_file:
                DB = json.load(in_file)
            return DB  # Pass database back
        else:  # Database dosen't exist then create database
            DB["_default"] = {}
            with open(Path, 'w') as out_file:
                json.dump(DB, out_file)
            return DB  # Pass database back

    # Load databases
    UPCDataBase = Start(UPCDataBasePath,UPCDataBase)
    ShippingDataBase = Start(ShippingDataBasePath, ShippingDataBase)
    AvgPriceDataBase = Start(AvgPriceDataBasePath, AvgPriceDataBase)
    ErrorsDataBase = Start(ErrorsDataBasePath, ErrorsDataBase)
    DisplayDataDataBase = Start(DisplayDataDataBasePath, DisplayDataDataBase)
    CallCountDataBase = Start(CallCountDataBasePath, CallCountDataBase)

    # Record initial database size, used to compare to end data base size at end of run
    InitialDataBaseSizes = [len(UPCDataBase["_default"].keys()),len(ShippingDataBase["_default"].keys()),len(AvgPriceDataBase["_default"].keys()),len(ErrorsDataBase["_default"].keys()),len(CallCountDataBase["_default"].keys())]

    print("Loaded")

# Called at the end of run, saves all database related things
def End():
    global UPCDataBase, ShippingDataBase, AvgPriceDataBase, ErrorsDataBase, DisplayDataDataBase, CallCountDataBase,DataBaseWrites,InitialDataBaseSizes

    # Save databases, note that commented out databases are not currently being used and saving them would overwrite the actual TinyDB database
    PushUPCDataBase()
    PushAvgDataBase()
    # PushCallDataBase()
    # PushDisplayDataBase()
    # PushErrorsDataBase()
    PushShippingDataBase()

    # Record size of database at end of run
    FinalDataBaseSizes = [len(UPCDataBase["_default"].keys()),len(ShippingDataBase["_default"].keys()),len(AvgPriceDataBase["_default"].keys()),len(ErrorsDataBase["_default"].keys()),len(CallCountDataBase["_default"].keys())]

    # Print difference between size of databases between beginning and end of run
    for a in range(len(InitialDataBaseSizes)):
        print(FinalDataBaseSizes[a]-InitialDataBaseSizes[a])

    print("Finished")


# Dump saves database DB to file located at Path
def Dump(Path,DB):
    with open(Path, 'w') as out_file:
        json.dump(DB, out_file)

# Push Database saves specific data base
def PushUPCDataBase():
    global UPCDataBase
    Dump(UPCDataBasePath,UPCDataBase)

def PushShippingDataBase():
    global ShippingDataBase
    Dump(ShippingDataBasePath, ShippingDataBase)

def PushAvgDataBase():
    global AvgPriceDataBase
    Dump(AvgPriceDataBasePath, AvgPriceDataBase)

def PushErrorsDataBase():
    global ErrorsDataBase
    Dump(ErrorsDataBasePath, ErrorsDataBase)

def PushDisplayDataBase():
    global DisplayDataDataBase
    Dump(DisplayDataDataBasePath, DisplayDataDataBase)

def PushCallDataBase():
    global CallCountDataBase
    Dump(CallCountDataBasePath, CallCountDataBase)


# Add adds an item to a database
def Add(Path,DB,Value):
    # In database {"1":data,"3":data,"NextNumber":Value} NextNumber has a value 1 higher than the current highest number
    nextNumber = (max([int(a) for a in DB["_default"].keys()]+[0])+1)
    DB["_default"][str(nextNumber)] = Value

    # If it is time to save database to file then save to file
    DataBaseWrites[Path] = DataBaseWrites[Path] + 1
    if(DataBaseWrites[Path] >= DatabaseWritesBeforePush):
        DataBaseWrites[Path] = 0  # Reset counter
        Dump(Path,DB)  # Save to file

# Add Value to Database for each database
def AddUPCDataBase(Value):
    global UPCDataBase
    Add(UPCDataBasePath,UPCDataBase,Value)

def AddShippingDataBase(Value):
    global ShippingDataBase
    Add(ShippingDataBasePath, ShippingDataBase,Value)

def AddAvgDataBase(Value):
    global AvgPriceDataBase
    # print("Adding to avg price " + str(Value))
    Add(AvgPriceDataBasePath, AvgPriceDataBase,Value)

def AddErrorsDataBase(Value):
    global ErrorsDataBase
    Add(ErrorsDataBasePath, ErrorsDataBase,Value)

def AddDisplayDataBase(Value):
    global DisplayDataDataBase
    Add(DisplayDataDataBasePath, DisplayDataDataBase,Value)

def AddCallDataBase(Value):
    global CallCountDataBase
    Add(CallCountDataBasePath, CallCountDataBase,Value)


# Find returns all items in the data base matching the Search Item dict
# If searching for item with Name = Bob and Value = Friendly then: SearchItem = {"Name":"Bob","Value":"Friendly"}
def Find(Path,DB,SearchItem):
    SearchValues = DB['_default']  # Informaion from database
    Results = []  # Initilize place for results to end up

    # Split keys and values apart to [[Name,Value],[Bob,Friendly]]
    SearchFor = [[a for a in SearchItem.keys()], [b for b in SearchItem.values()]]
    for ItemIndex in SearchValues:  # Go through all values in database
        for SearchIndex in range(len(SearchFor[0])):  # Go through all key-value combos in SearchFor
            SearchingForKey = SearchFor[0][SearchIndex]  # Grab key to compare
            SearchingForValue = SearchFor[1][SearchIndex]  # Grab value to compare

            # If key-value combo is not in ItemIndex, move to next item
            if(SearchingForKey not in SearchValues[ItemIndex].keys() or SearchValues[ItemIndex][SearchingForKey] != SearchingForValue): break
            elif(SearchIndex == len(SearchFor[0])-1):  # Key value combo in and run out of key value combos
                Results.append(SearchValues[ItemIndex])  # This is a hit

            # Key-Value combo in search, but there are still more key-value combos to check before it can be called a result

    return Results

# Find Value in database for each database
def FindUPCDataBase(Value):
    global UPCDataBase
    return Find(UPCDataBasePath,UPCDataBase,Value)

def FindShippingDataBase(Value):
    global ShippingDataBase
    return Find(ShippingDataBasePath, ShippingDataBase,Value)

def FindAvgDataBase(Value):
    global AvgPriceDataBase
    return Find(AvgPriceDataBasePath, AvgPriceDataBase,Value)

def FindErrorsDataBase(Value):
    global ErrorsDataBase
    return Find(ErrorsDataBasePath, ErrorsDataBase,Value)

def FindDisplayDataBase(Value):
    global DisplayDataDataBase
    return Find(DisplayDataDataBasePath, DisplayDataDataBase,Value)

def FindCallDataBase(Value):
    global CallCountDataBase
    return Find(CallCountDataBasePath, CallCountDataBase,Value)


# Clear removes everying from database and initilizes default state {"_default"{}}
def Clear(Path,DB):
    DB = {}  # Create default state
    DB["_default"] = {}

    with open(Path, 'w') as out_file:  # Save default state to file
        json.dump(DB, out_file)
    return DB  # Pass default state to global database


# Clear database for all databases
def ClearUPCDataBase():
    global UPCDataBase
    UPCDataBase = Clear(UPCDataBasePath,UPCDataBase)

def ClearShippingDataBase():
    global ShippingDataBase
    ShippingDataBase = Clear(ShippingDataBasePath, ShippingDataBase)

def ClearAvgDataBase():
    global AvgPriceDataBase
    AvgPriceDataBase = Clear(AvgPriceDataBasePath, AvgPriceDataBase)

def ClearErrorsDataBase():
    global ErrorsDataBase
    ErrorsDataBase = Clear(ErrorsDataBasePath, ErrorsDataBase)

def ClearDisplayDataBase():
    global DisplayDataDataBase
    DisplayDataDataBase = Clear(DisplayDataDataBasePath, DisplayDataDataBase)

def ClearCallDataBase():
    global CallCountDataBase
    CallCountDataBase = Clear(CallCountDataBasePath, CallCountDataBase)


# Remove first item from data base matching some value, if you want to remove the first thing with name bob, then
# RemoveItem = {"Name":"bob"}
def Remove(Path,DB,RemoveItem):
    ItemPop = None  # Initilize value to see if item remove successfull
    print(len(DB["_default"].keys()))

    SearchValues = DB['_default']
    SearchFor = [[a for a in RemoveItem.keys()], [b for b in RemoveItem.values()]]  # Key-Value comparision combo
    for ItemIndex in SearchValues:  # Go through all items in database
        for SearchIndex in range(len(SearchFor[0])):  # Go through all key-value comboes
            SearchingForKey = SearchFor[0][SearchIndex]
            SearchingForValue = SearchFor[1][SearchIndex]

            # If key-value dosen't match then move onto next Item in database
            if(SearchingForKey not in SearchValues[ItemIndex].keys() or SearchValues[ItemIndex][SearchingForKey] != SearchingForValue): break
            # If key-value does match and no more key-value combos to check then item to remove was found
            elif(SearchIndex == len(SearchFor[0])-1):
                ItemPop = ItemIndex  # Item to removes position in database
            # Key value found but there are still more key values to check

    if(ItemPop != None):  # If Item was found to remove
        print("Success")
        DB["_default"].pop(ItemPop)  # Remove Item
        Success = True  # Value returned
    else:
        Success = False  # If no item was found return false

    # Check if database needs to be written to
    global DataBaseWrites
    DataBaseWrites[Path] = DataBaseWrites[Path] + 1
    if (DataBaseWrites[Path] >= DatabaseWritesBeforePush):
        DataBaseWrites[Path] = 0
        Dump(Path, DB)

    return Success,DB  # Return True/False if item pop successfull and database with item removed

# Remove for all databases
def RemoveUPCDataBase(RemoveObject):
    global UPCDataBase
    Success, UPCDataBase = Remove(UPCDataBasePath,UPCDataBase,RemoveObject)

def RemoveShippingDataBase(RemoveObject):
    global ShippingDataBase
    Success, ShippingDataBase =  Remove(ShippingDataBasePath, ShippingDataBase,RemoveObject)
    return Success

def RemoveAvgDataBase(RemoveObject):
    global AvgPriceDataBase
    Success, AvgPriceDataBase =  Remove(AvgPriceDataBasePath, AvgPriceDataBase,RemoveObject)
    return Success

def RemoveErrorsDataBase(RemoveObject):
    global ErrorsDataBase
    Success, ErrorsDataBase =  Remove(ErrorsDataBasePath, ErrorsDataBase,RemoveObject)
    return Success

def RemoveDisplayDataBase(RemoveObject):
    global DisplayDataDataBase
    Success, DisplayDataDataBase =  Remove(DisplayDataDataBasePath, DisplayDataDataBase,RemoveObject)
    return Success

def RemoveCallDataBase(RemoveObject):
    global CallCountDataBase
    Success, CallCountDataBase =  Remove(CallCountDataBasePath, CallCountDataBase,RemoveObject)
    return Success


# All returns the entire database structure
def All(Path,DB):
    return DB["_default"]

def AllUPCDataBase():
    global UPCDataBase
    return All(UPCDataBasePath,UPCDataBase)

def AllShippingDataBase():
    global ShippingDataBase
    return All(ShippingDataBasePath, ShippingDataBase)

def AllAvgDataBase():
    global AvgPriceDataBase
    return All(AvgPriceDataBasePath, AvgPriceDataBase)

def AllErrorsDataBase():
    global ErrorsDataBase
    return All(ErrorsDataBasePath, ErrorsDataBase)

def AllDisplayDataBase():
    global DisplayDataDataBase
    return All(DisplayDataDataBasePath, DisplayDataDataBase)

def AllCallDataBase():
    global CallCountDataBase
    return All(CallCountDataBasePath, CallCountDataBase)


# Incriment incriments the first value that is located by searchItem
def Incriment(Path,DB,ValueToIncriment,SearchItem):
    SearchValues = DB['_default']

    SearchFor = [[a for a in SearchItem.keys()], [b for b in SearchItem.values()]]  # Key-Value Combo
    for ItemIndex in SearchValues:  # Searches all items in database
        for SearchIndex in range(len(SearchFor[0])):  # Searches all key-value combos
            SearchingForKey = SearchFor[0][SearchIndex]
            SearchingForValue = SearchFor[1][SearchIndex]

            # If key-value not found in current searching item move onto next item
            if (SearchingForKey not in SearchValues[ItemIndex].keys() or SearchValues[ItemIndex][
                SearchingForKey] != SearchingForValue):
                break
            # Found value to incriment
            elif (SearchIndex == len(SearchFor[0]) - 1):
                # Incriment value
                SearchValues[ItemIndex][ValueToIncriment] = int(SearchValues[ItemIndex][ValueToIncriment]) + 1
            # key-value found but still have more key-value combos to check

    # Check if database needs to be saved
    DataBaseWrites[Path] = DataBaseWrites[Path] + 1
    if (DataBaseWrites[Path] >= DatabaseWritesBeforePush):
        DataBaseWrites[Path] = 0
        Dump(Path, DB)

    return DB

# Incriment for all databases
def IncrimentUPCDataBase(ValueToIncriment,SearchItem):
    global UPCDataBase
    UPCDataBase = Incriment(UPCDataBasePath,UPCDataBase,ValueToIncriment,SearchItem)

def IncrimentShippingDataBase(ValueToIncriment,SearchItem):
    global ShippingDataBase
    ShippingDataBase = Incriment(ShippingDataBasePath, ShippingDataBase,ValueToIncriment,SearchItem)

def IncrimentAvgDataBase(ValueToIncriment,SearchItem):
    global AvgPriceDataBase
    AvgPriceDataBase = Incriment(AvgPriceDataBasePath, AvgPriceDataBase,ValueToIncriment,SearchItem)

def IncrimentErrorsDataBase(ValueToIncriment,SearchItem):
    global ErrorsDataBase
    ErrorsDataBase = Incriment(ErrorsDataBasePath, ErrorsDataBase,ValueToIncriment,SearchItem)

def IncrimentDisplayDataBase(ValueToIncriment,SearchItem):
    global DisplayDataDataBase
    DisplayDataDataBase = Incriment(DisplayDataDataBasePath, DisplayDataDataBase,ValueToIncriment,SearchItem)

def IncrimentCallDataBase(ValueToIncriment,SearchItem):
    global CallCountDataBase
    CallCountDataBase = Incriment(CallCountDataBasePath, CallCountDataBase,ValueToIncriment,SearchItem)

# When program stops save all data
@atexit.register
def OnExit():
    End()  # Saves all data

# Tests database write speed
def Test():
    ClearErrorsDataBase()

    import time
    for i in range(100):
        StartTime = time.time()
        for a in range(100):
            AddErrorsDataBase({"Name":str(i*a),"Value1":i,"Value2":a-10})
        CycleTime = time.time()-StartTime
        print(CycleTime)

    for i in range(100):
        print(FindErrorsDataBase({"Name":str(i*20)}))

Startup()  # Initilize database
