#!/bin/bash

openssl s_client -connect smtp.office365.com:587 -crlf -starttls smtp 


helo
auth login
$(echo -n mail@something.de |base64)
$(echo -n XXX |base64)
mail from:mail@something.de
rcpt to:mail@something.de
DATA
FROM:  mail@something.de
TO: mail@something.de
SUBJECT: TEST
DATATATATTA


