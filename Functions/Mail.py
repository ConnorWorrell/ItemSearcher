import ssl
import smtplib
import os
import time
import json

########################################################################################################################
# Mail.py
#
# Mail has one function Send
#
# Send(["LinesOfText"]) Sends a email from the sender_email with a password and smtp_server to the reciever_email
# those addresses are stored in Database/PasswordsAndSuch
#
########################################################################################################################

# Initialization

# Load the json file stored in Database/PasswordsAndSuch
PasswordsFile = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/PasswordsAndSuch'
with open(PasswordsFile, 'r') as in_file:
    Passwords = json.load(in_file)

# Get information out of json file
smtp_server = Passwords['smtp_server'] #eg: smtp.gmail.com
sender_email = Passwords['sender_email']
receiver_email = Passwords['receiver_email']
password = Passwords['password']

def Send(Text):
    port = 587  # For starttls

    message = ''
    Text.insert(0,'Subject: Ebay Deals!\n')  # Email subject line

    # Load mail log folder position
    MailLogPath = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Mail/'
    MailLogPosition = MailLogPath + str(time.time()) + ".txt"

    if not os.path.exists(MailLogPath):  # If LOGS/Mail folder dosen't exist create it
        os.makedirs(MailLogPath)

    for Line in Text:  # Assemble text array into the message file
        with open(MailLogPosition, 'a') as f:
            f.write("%s\n" % (str(Line)))
        f.close()

        message = message + Line + "\n"

    # Connect to smpt server and send email
    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
