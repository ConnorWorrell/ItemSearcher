import os
import json
import atexit

UPCDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToUPC"
ShippingDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToShipping"
AvgPriceDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/LinkToAvgPrice"
ErrorsDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/Logs/Errorss"
DisplayDataDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/DisplayData.txt"
CallCountDataBasePath = os.path.dirname(os.path.dirname(__file__)) + "/DataBase/CallCount"

UPCDataBase = {}
ShippingDataBase = {}
AvgPriceDataBase = {}
ErrorsDataBase = {}
DisplayDataDataBase = {}
CallCountDataBase = {}

DatabaseWritesBeforePush = 100
DataBaseWrites = {}

def Startup():
    global UPCDataBase, ShippingDataBase, AvgPriceDataBase, ErrorsDataBase, DisplayDataDataBase, CallCountDataBase,DataBaseWrites,InitialDataBaseSizes

    def Start(Path,DB):
        DataBaseWrites[Path] = 0
        if (os.path.exists(Path)):
            with open(Path, 'r') as in_file:
                DB = json.load(in_file)
            return DB
        else:
            DB["_default"] = {}
            with open(Path, 'w') as out_file:
                json.dump(DB, out_file)
            return DB

    UPCDataBase = Start(UPCDataBasePath,UPCDataBase)
    ShippingDataBase = Start(ShippingDataBasePath, ShippingDataBase)
    AvgPriceDataBase = Start(AvgPriceDataBasePath, AvgPriceDataBase)
    ErrorsDataBase = Start(ErrorsDataBasePath, ErrorsDataBase)
    DisplayDataDataBase = Start(DisplayDataDataBasePath, DisplayDataDataBase)
    CallCountDataBase = Start(CallCountDataBasePath, CallCountDataBase)

    # print(len(UPCDataBase["_default"].keys()))
    InitialDataBaseSizes = [len(UPCDataBase["_default"].keys()),len(ShippingDataBase["_default"].keys()),len(AvgPriceDataBase["_default"].keys()),len(ErrorsDataBase["_default"].keys()),len(CallCountDataBase["_default"].keys())]

    print("Loaded")

def End():
    global UPCDataBase, ShippingDataBase, AvgPriceDataBase, ErrorsDataBase, DisplayDataDataBase, CallCountDataBase,DataBaseWrites,InitialDataBaseSizes
    PushUPCDataBase()
    PushAvgDataBase()
    # PushCallDataBase()
    # PushDisplayDataBase()
    # PushErrorsDataBase()
    PushShippingDataBase()

    FinalDataBaseSizes = [len(UPCDataBase["_default"].keys()),len(ShippingDataBase["_default"].keys()),len(AvgPriceDataBase["_default"].keys()),len(ErrorsDataBase["_default"].keys()),len(CallCountDataBase["_default"].keys())]

    for a in range(len(InitialDataBaseSizes)):
        print(FinalDataBaseSizes[a]-InitialDataBaseSizes[a])

    print("Finished")



def Dump(Path,DB):
    # print("Dumping to " + str(Path) + "  |  " + str(DB))
    with open(Path, 'w') as out_file:
        json.dump(DB, out_file)

def PushUPCDataBase():
    global UPCDataBase
    # print("Push")
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

def Add(Path,DB,Value):
    nextNumber = (max([int(a) for a in DB["_default"].keys()]+[0])+1)
    DB["_default"][str(nextNumber)] = Value

    DataBaseWrites[Path] = DataBaseWrites[Path] + 1
    if(DataBaseWrites[Path] >= DatabaseWritesBeforePush):
        DataBaseWrites[Path] = 0
        Dump(Path,DB)

def AddUPCDataBase(Value):
    global UPCDataBase
    # print("Add")
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


def Find(Path,DB,SearchItem):
    SearchValues = DB['_default']
    Results = []

    SearchFor = [[a for a in SearchItem.keys()], [b for b in SearchItem.values()]]
    for ItemIndex in SearchValues:

        for SearchIndex in range(len(SearchFor[0])):
            SearchingForKey = SearchFor[0][SearchIndex]
            SearchingForValue = SearchFor[1][SearchIndex]
            if(SearchingForKey not in SearchValues[ItemIndex].keys() or SearchValues[ItemIndex][SearchingForKey] != SearchingForValue): break
            elif(SearchIndex == len(SearchFor[0])-1):
                Results.append(SearchValues[ItemIndex])

    return Results

def FindUPCDataBase(Value):
    global UPCDataBase
    # print("Find")
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


def Clear(Path,DB):
    DB = {}
    DB["_default"] = {}
    with open(Path, 'w') as out_file:
        json.dump(DB, out_file)
    return DB

def ClearUPCDataBase():
    global UPCDataBase
    # print("Clear")
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


def Remove(Path,DB,RemoveItem):
    ItemPop = None
    print(len(DB["_default"].keys()))

    SearchValues = DB['_default']
    SearchFor = [[a for a in RemoveItem.keys()], [b for b in RemoveItem.values()]]
    for ItemIndex in SearchValues:

        for SearchIndex in range(len(SearchFor[0])):
            SearchingForKey = SearchFor[0][SearchIndex]
            SearchingForValue = SearchFor[1][SearchIndex]
            if(SearchingForKey not in SearchValues[ItemIndex].keys() or SearchValues[ItemIndex][SearchingForKey] != SearchingForValue): break
            elif(SearchIndex == len(SearchFor[0])-1):
                ItemPop = ItemIndex

    if(ItemPop != None):
        print("Success")
        DB["_default"].pop(ItemPop)
        Success = True
    else:
        Success = False

    global DataBaseWrites
    DataBaseWrites[Path] = DataBaseWrites[Path] + 1
    if (DataBaseWrites[Path] >= DatabaseWritesBeforePush):
        DataBaseWrites[Path] = 0
        Dump(Path, DB)

    print(len(DB["_default"].keys()))
    return Success,DB

def RemoveUPCDataBase(RemoveObject):
    global UPCDataBase
    # print("Remove")
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


def All(Path,DB):
    return DB["_default"]


def AllUPCDataBase():
    print("All")
    global UPCDataBase
    UPCDataBase = All(UPCDataBasePath,UPCDataBase)

def AllShippingDataBase():
    global ShippingDataBase
    ShippingDataBase = All(ShippingDataBasePath, ShippingDataBase)

def AllAvgDataBase():
    global AvgPriceDataBase
    AvgPriceDataBase = All(AvgPriceDataBasePath, AvgPriceDataBase)

def AllErrorsDataBase():
    global ErrorsDataBase
    ErrorsDataBase = All(ErrorsDataBasePath, ErrorsDataBase)

def AllDisplayDataBase():
    global DisplayDataDataBase
    DisplayDataDataBase = All(DisplayDataDataBasePath, DisplayDataDataBase)

def AllCallDataBase():
    global CallCountDataBase
    CallCountDataBase = All(CallCountDataBasePath, CallCountDataBase)

def Update(Path,DB,ValueToIncriment,SearchItem):
    SearchValues = DB['_default']
    Results = []

    SearchFor = [[a for a in SearchItem.keys()], [b for b in SearchItem.values()]]
    for ItemIndex in SearchValues:

        for SearchIndex in range(len(SearchFor[0])):
            SearchingForKey = SearchFor[0][SearchIndex]
            SearchingForValue = SearchFor[1][SearchIndex]
            if (SearchingForKey not in SearchValues[ItemIndex].keys() or SearchValues[ItemIndex][
                SearchingForKey] != SearchingForValue):
                break
            elif (SearchIndex == len(SearchFor[0]) - 1):
                SearchValues[ItemIndex][ValueToIncriment] = int(SearchValues[ItemIndex][ValueToIncriment]) + 1

    DataBaseWrites[Path] = DataBaseWrites[Path] + 1
    if (DataBaseWrites[Path] >= DatabaseWritesBeforePush):
        DataBaseWrites[Path] = 0
        Dump(Path, DB)

def UpdateUPCDataBase(ValueToIncriment,SearchItem):
    global UPCDataBase
    UPCDataBase = Update(UPCDataBasePath,UPCDataBase,ValueToIncriment,SearchItem)

def UpdateShippingDataBase(ValueToIncriment,SearchItem):
    global ShippingDataBase
    ShippingDataBase = Update(ShippingDataBasePath, ShippingDataBase,ValueToIncriment,SearchItem)

def UpdateAvgDataBase(ValueToIncriment,SearchItem):
    global AvgPriceDataBase
    AvgPriceDataBase = Update(AvgPriceDataBasePath, AvgPriceDataBase,ValueToIncriment,SearchItem)

def UpdateErrorsDataBase(ValueToIncriment,SearchItem):
    global ErrorsDataBase
    ErrorsDataBase = Update(ErrorsDataBasePath, ErrorsDataBase,ValueToIncriment,SearchItem)

def UpdateDisplayDataBase(ValueToIncriment,SearchItem):
    global DisplayDataDataBase
    DisplayDataDataBase = Update(DisplayDataDataBasePath, DisplayDataDataBase,ValueToIncriment,SearchItem)

def UpdateCallDataBase(ValueToIncriment,SearchItem):
    global CallCountDataBase
    CallCountDataBase = Update(CallCountDataBasePath, CallCountDataBase,ValueToIncriment,SearchItem)

@atexit.register
def OnExit():
    End()

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

Startup()
# ClearErrorsDataBase()
# AddErrorsDataBase({"Test":"hi3"})
# RemoveErrorsDataBase({"Test":"hi3"})