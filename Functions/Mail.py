import ssl
import smtplib
import os
import time
import json

PasswordsFile = str(os.path.dirname(os.path.dirname(__file__))) + '/DataBase/PasswordsAndSuch'
with open(PasswordsFile, 'r') as in_file:
    Passwords = json.load(in_file)

smtp_server = Passwords['smtp_server'] #eg: smtp.gmail.com
sender_email = Passwords['sender_email']
receiver_email = Passwords['receiver_email']
password = Passwords['password']

def Send(Text):
    port = 587  # For starttls


    message = ''
    Text.insert(0,'Subject: Ebay Deals!\n')

    LogPosition = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Mail/' + str(time.time()) + ".txt"
    LogPath = str(os.path.dirname(os.path.dirname(__file__))) + '/LOGS/Mail/'

    if not os.path.exists(LogPath):
        os.makedirs(LogPath)

    for Line in Text:
        with open(LogPosition, 'a') as f:
            f.write("%s\n" % (str(Line)))
        f.close()

        message = message + Line + "\n"

    context = ssl.create_default_context()
    with smtplib.SMTP(smtp_server, port) as server:
        server.ehlo()  # Can be omitted
        server.starttls(context=context)
        server.ehlo()  # Can be omitted
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
