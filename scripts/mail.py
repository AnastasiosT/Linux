#!/usr/bin/python3

import smtplib
## https://docs.python.org/3/library/smtplib.html 


sender = "mail@something.de"
receiver = ["mail@something.de"]
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
