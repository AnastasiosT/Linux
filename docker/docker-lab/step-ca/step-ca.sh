#!/bin/bash
echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/00-docker
echo 'APT::Install-Recommends "0";' >> /etc/apt/apt.conf.d/00-docker
DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3  vim xinetd iputils-ping nmap wget\
  && rm -rf /var/lib/apt/lists/*


#variables for the script
rootca="test-THANOS-CA"
san1="localhost"
servercrt="test-it-us-0003"
intermediateca="test-THANOS-Intermediate"
san2="127.0.1.1"
san3="10.0.0.12"
san4="it-us-0003"

echo $rootca $san1 $san2 $san2 $san3 $san4 $servercrt $intermediateca

# Install step cli and step ca
wget https://dl.step.sm/gh-release/cli/docs-cli-install/v0.23.1/step-cli_0.23.1_amd64.deb --no-check-certificate
dpkg -i step-cli_0.23.1_amd64.deb
wget https://dl.step.sm/gh-release/certificates/docs-ca-install/v0.23.1/step-ca_0.23.1_amd64.deb --no-check-certificate
dpkg -i step-ca_0.23.1_amd64.deb

# create the CA

step certificate create --kty RSA --profile root-ca $rootca /home/step/$rootca.crt /home/step/$rootca.key --san=$san1 --san=$san2 --san=$san3 --san=$san4 --password-file=/home/step/pw 

#--not-before=87660h

# create the intermediate CA

step certificate create --kty RSA $intermediateca     /home/step/$intermediateca.crt /home/step/$intermediateca.key     --profile intermediate-ca --ca /home/step/$rootca.crt --ca-key /home/step/$rootca.key --ca-password-file=/home/step/pw --password-file=/home/step/pw


# create the certificate

step certificate create --kty RSA $servercrt /home/step/$servercrt.crt /home/step/$servercrt.key  --profile leaf --not-after=87660h  --ca /home/step/$intermediateca.crt --ca-key /home/step/$intermediateca.key --bundle --san=$san1 --san=$san2 --san=$san3 --san=$san4 --password-file=home/step/pw --ca-password-file=/home/step/pw

#step ca init --deployment-type=standalone --name=thanos --dns=$(hostname -f) --address=:9443 --provisioner=thanos --password-file=/home/step/pwintermediateca.key


#start the CA

#step-ca $(step path)/config/ca.json --password-file=/home/step/pw


##update the provisioner

#step ca provisioner update thanos    --x509-min-dur=20m    --x509-max-dur=87660h    --x509-default-dur=87660h

##

while true; do
  sleep 10000
done


