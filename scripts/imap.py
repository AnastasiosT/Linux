#!/usr/bin/python3

import imaplib

user = 'mail@mail.de'
password = 'XXX!'
host = 'imap.host.de'

# Connect securely with SSL
imap = imaplib.IMAP4_SSL(host)

## Login to remote server
imap.login(user, password)

imap.select('Inbox')

tmp, messages = imap.search(None, 'ALL')
for num in messages[0].split():
	# Retrieve email message by ID
	tmp, data = imap.fetch(num, '(RFC822)')
	print('Message: {0}\n'.format(data[0][1]))
	break
	
imap.close()
imap.logout()
