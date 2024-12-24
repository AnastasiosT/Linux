#!/usr/bin/python3

# this script will use starttls and port 587 to connect to smtp

import smtplib
import ssl
## https://docs.python.org/3/library/smtplib.html 


sender = "mail@something.de"
receiver = ["mail@something.de"]

message = "Subject: Test Email\n\nHello!"

try:
    # Create SSL context
    ssl_context = ssl.create_default_context()

    # Establish connection
    session = smtplib.SMTP('smtp.strato.de', 587)
    session.set_debuglevel(2)  # Enable debug output
    session.ehlo()
    session.starttls(context=ssl_context)  # Upgrade to secure TLS
    session.ehlo()
    session.login(sender, 'PW')

    # Send email
    session.sendmail(sender, receiver, message)
    print("Email sent successfully.")
    session.quit()

except smtplib.SMTPException as e:
    print(f'SMTP error occurred: {e}')
except Exception as e:
    print(f'An error occurred: {e}')
