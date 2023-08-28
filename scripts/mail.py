#!/usr/bin/python3

import smtplib

sender = "anastasios-thomaidis@tt-bezirk-stuttgart.de"
receiver = ["adam.kangiser@checkmk.com"]
message = "Hello!"

try:
    session = smtplib.SMTP('smtp.office365.com',587)
    session.set_debuglevel(2)
    session.ehlo()
    session.starttls()
    session.ehlo()
    session.login(sender,'XXX')
    session.sendmail(sender,receiver,message)
    session.quit()

except smtplib.SMTPException:
    print('Error')
