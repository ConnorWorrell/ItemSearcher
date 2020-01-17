from tinydb import TinyDB, Query
import os
import pickledb
import ZODB,ZODB.FileStorage
import dataset
import time
import sys

ItemCount = 5000

def TestTinyDB():
    print("TinyDB:")
    db = TinyDB(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/TestTinydb")
    #db.purge_tables()

    StartTime = time.time()
    for i in range(ItemCount):
        db.insert({'hi':'test','value':i})
        sys.stdout.write("\ri %d" % i)
    print("\n" + str((time.time() - StartTime) / ItemCount))

def TestPickleDB():
    print("PickleDB:")
    db = pickledb.load(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/TestPickledb", False)
    StartTime = time.time()
    for i in range(ItemCount):
       # print(i)
        db.set(str(i), i)
        sys.stdout.write("\ri %d" % i)
    print("\n" + str((time.time() - StartTime) / ItemCount))
    db.dump()

# def TestZODB():
#     storage = ZODB.FileStorage.FileStorage(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/ZODB/ZODB")
#     db = ZODB.DB(storage)
#     connection = db.open()
#     root = connection.root
#     root.Test1[0] = "hi"
#
#     root.commit()
#

#     print(root.Test1[0])

def TestDataSetDB():
    print("DataSetDB:")
    db = dataset.connect('sqlite:///' + str(os.path.dirname(os.path.dirname(__file__)) + "/DataBase/TestDatasetDB"))
    table = db['Table']

    StartTime = time.time()

    for i in range(ItemCount):
        table.insert(dict(hi='2',p='c'))
        sys.stdout.write("\ri %d" % i)
    print("\n" + str((time.time() - StartTime) / ItemCount))



TestTinyDB()
TestPickleDB()
TestDataSetDB()