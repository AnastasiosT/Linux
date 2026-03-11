#!/bin/bash

(
#sleep 5
echo "EHLO localhost"
sleep 1
echo "AUTH LOGIN"
sleep 1
echo "$(echo -n "mail@something.de" | base64)"
sleep 1
echo "$(echo -n "mailPW" | base64)"
sleep 1
echo "MAIL FROM:<mail@something.de>"
sleep 1
echo "rcpt to:<mail@something.de>"
sleep 1
echo "DATA"
sleep 1
echo "From: mail@something.de"
echo "To: mail@something.de"
echo "Subject: TEST"
echo ""
echo "DATATATATTA"
echo "."
sleep 1
echo "QUIT"
) | openssl s_client -connect smtp.strato.de:465 -crlf
