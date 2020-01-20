import os
import time

########################################################################################################################
# Logs.py
#
# Logs contains 2 functions New and Write,
# Logs.New() will create a new log file in the logs/runtime folder and,
# Logs.Write("Text to be written") will write a new line to the last log file
########################################################################################################################

#Initilization
LogPath = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/'  # Path to log folder
# If folder dosen't exist create it
if not os.path.exists(str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/'):
    os.makedirs(str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/')

try:  # Try to find previous log file and place it into Log Position variable
    # Name of the log file is the unix time of its original creation, previous log file is the file with the largest
    # floating point name, Log Name gets a list of the file names, removes .txt and finds the largest float
    LogName = str(max([float(s.replace('.txt', '')) for s in os.listdir(str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/')]))
    LogPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/' + LogName + ".txt"
except:  # If unable to find previous log file then Log Position is None, to be set when New or Write are called
    LogPosition = None
    pass


# Logs.New() will create a new log file in the logs/runtime folder
def New():
    global LogPosition # File location of the current log
    # Create new log location
    LogPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Runtime/' + str(time.time()) + '.txt'
    with open(LogPosition, 'w') as f:
        for item in []:  # Write Empty Log File
            f.write("%s\n" % item)
        f.close()


# Logs.Write("Text to be written") will write a new line to the last log file
def Write(Data):
    global LogPosition  # Grab location of log file

    if(LogPosition == None):  # If no previous log file exists create a new log file
        New()

    with open(LogPosition, 'a') as f:  # Write data to new line in log file, encode/decode to force ascii characters
        f.write("%s %s\n" % (str(time.time()),str(Data).encode('ascii','ignore').decode()))
    f.close()
