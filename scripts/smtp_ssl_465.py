#!/usr/bin/python3


#this scripr will use tls and port 465 to connect to smtp

import smtplib
from email.mime.text import MIMEText  # For creating email messages
from email.mime.multipart import MIMEMultipart  # For complex messages

# Sender and receiver details
sender = "mail@something.de"
receiver = ["mail@something.de"]
password = "XXX"

# Create the email
subject = "Test Email"
body = "Hello!"
message = MIMEMultipart()
message['From'] = sender
message['To'] = ", ".join(receiver)
message['Subject'] = subject
message.attach(MIMEText(body, 'plain'))

try:
    # Establish a secure SMTP connection
    with smtplib.SMTP_SSL('smtp.strato.de', 465) as session:
        session.set_debuglevel(1)  # Debugging information printed to the console
        session.login(sender, password)
        session.sendmail(sender, receiver, message.as_string())
        print("Email sent successfully.")
except smtplib.SMTPException as e:
    print(f"Error: {e}")
