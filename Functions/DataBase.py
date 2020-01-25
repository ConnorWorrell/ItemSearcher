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
    global UPCDataBase, ShippingDataBase, AvgPriceDataBase, ErrorsDataBase, DisplayDataDataBase, CallCountDataBase,DataBaseWrites

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

    ErrorsDataBase = Start(UPCDataBasePath,UPCDataBase)
    ShippingDataBase = Start(ShippingDataBasePath, ShippingDataBase)
    AvgPriceDataBase = Start(AvgPriceDataBasePath, AvgPriceDataBase)
    ErrorsDataBase = Start(ErrorsDataBasePath, ErrorsDataBase)
    DisplayDataDataBase = Start(DisplayDataDataBasePath, DisplayDataDataBase)
    CallCountDataBase = Start(CallCountDataBasePath, CallCountDataBase)

    print("Loaded")

def End():
    PushUPCDataBase()
    PushAvgDataBase()
    PushCallDataBase()
    PushDisplayDataBase()
    PushErrorsDataBase()
    PushShippingDataBase()

    print("Finished")



def Dump(Path,DB):
    with open(Path, 'w') as out_file:
        json.dump(DB, out_file)

def PushUPCDataBase():
    Dump(UPCDataBasePath,UPCDataBase)

def PushShippingDataBase():
    Dump(ShippingDataBasePath, ShippingDataBase)

def PushAvgDataBase():
    Dump(AvgPriceDataBasePath, AvgPriceDataBase)

def PushErrorsDataBase():
    Dump(ErrorsDataBasePath, ErrorsDataBase)

def PushDisplayDataBase():
    Dump(DisplayDataDataBasePath, DisplayDataDataBase)

def PushCallDataBase():
    Dump(CallCountDataBasePath, CallCountDataBase)



def Add(Path,DB,Value):
    DB["_default"][str(len(DB["_default"]) + 1)] = Value

    DataBaseWrites[Path] = DataBaseWrites[Path] + 1
    if(DataBaseWrites[Path] >= DatabaseWritesBeforePush):
        Dump(Path,DB)

def AddUPCDataBase(Value):
    Add(UPCDataBasePath,UPCDataBase,Value)

def AddShippingDataBase(Value):
    Add(ShippingDataBasePath, ShippingDataBase,Value)

def AddAvgDataBase(Value):
    Add(AvgPriceDataBasePath, AvgPriceDataBase,Value)

def AddErrorsDataBase(Value):
    Add(ErrorsDataBasePath, ErrorsDataBase,Value)

def AddDisplayDataBase(Value):
    Add(DisplayDataDataBasePath, DisplayDataDataBase,Value)

def AddCallDataBase(Value):
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
    return Find(UPCDataBasePath,UPCDataBase,Value)

def FindShippingDataBase(Value):
    return Find(ShippingDataBasePath, ShippingDataBase,Value)

def FindAvgDataBase(Value):
    return Find(AvgPriceDataBasePath, AvgPriceDataBase,Value)

def FindErrorsDataBase(Value):
    return Find(ErrorsDataBasePath, ErrorsDataBase,Value)

def FindDisplayDataBase(Value):
    return Find(DisplayDataDataBasePath, DisplayDataDataBase,Value)

def FindCallDataBase(Value):
    return Find(CallCountDataBasePath, CallCountDataBase,Value)


def Clear(Path,DB):
    DB = {}
    DB["_default"] = {}
    with open(Path, 'w') as out_file:
        json.dump(DB, out_file)
    return DB

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


def Remove(Path,DB,RemoveItem):
    ItemPop = None
    for Item in DB["_default"]:
        if(DB["_default"][Item] == RemoveItem):
            ItemPop = [Item,DB["_default"][Item]]
            break
    if(ItemPop != None):
        DB["_default"].pop(ItemPop[0])
        return True
    else:
        return False

def RemoveUPCDataBase(RemoveObject):
    return Remove(UPCDataBasePath,UPCDataBase,RemoveObject)

def RemoveShippingDataBase(RemoveObject):
    return Remove(ShippingDataBasePath, ShippingDataBase,RemoveObject)

def RemoveAvgDataBase(RemoveObject):
    return Remove(AvgPriceDataBasePath, AvgPriceDataBase,RemoveObject)

def RemoveErrorsDataBase(RemoveObject):
    return Remove(ErrorsDataBasePath, ErrorsDataBase,RemoveObject)

def RemoveDisplayDataBase(RemoveObject):
    return Remove(DisplayDataDataBasePath, DisplayDataDataBase,RemoveObject)

def RemoveCallDataBase(RemoveObject):
    return Remove(CallCountDataBasePath, CallCountDataBase,RemoveObject)

@atexit.register
def OnExit():
    End()

Startup()

