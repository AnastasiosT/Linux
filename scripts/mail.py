#!/usr/bin/python3

import smtplib

sender = "anastasios-thomaidis@tt-bezirk-stuttgart.de"
receiver = ["anastasios.thomaidis@checkmk.com"]
message = "Hello!"

try:
    session = smtplib.SMTP('smtp.office365.com',587)
    session.ehlo()
    session.starttls()
    session.ehlo()
    session.login(sender,'Office365@Stuttgart')
    session.sendmail(sender,receiver,message)
    session.quit()

except smtplib.SMTPException:
    print('Error')
