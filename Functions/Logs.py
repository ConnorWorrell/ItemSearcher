import os
import time
#os.path.dirname(os.path.dirname(__file__))


def New():
    global LogPosition
    LogPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/' + str(time.time()) + '.txt'
    print(LogPosition)
    with open(LogPosition, 'w') as f:
        for item in []:
            f.write("%s\n" % item)
        f.close()

LogName = str(max([float(s.replace('.txt', '')) for s in os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/')]))
LogPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/' + LogName + ".txt"

def Write(Data):

    global LogPosition
    with open(LogPosition, 'a') as f:

        f.write("%s %s\n" % (str(time.time()),str(Data).encode('ascii','ignore').decode()))
    f.close()
