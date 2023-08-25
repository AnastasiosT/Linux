#!/bin/bash

openssl s_client -connect smtp.office365.com:587 -crlf -starttls smtp 


helo
auth login
$(echo -n anastasios-thomaidis@tt-bezirk-stuttgart.de |base64)
$(echo -n XXX |base64)
mail from:anastasios-thomaidis@tt-bezirk-stuttgart.de
rcpt to:anastasios.thomaidis@checkmk.com
DATA
FROM:  anastasios-thomaidis@tt-bezirk-stuttgart.de
TO: anastasios.thomaidis@checkmk.com
SUBJECT: TEST
DATATATATTA


