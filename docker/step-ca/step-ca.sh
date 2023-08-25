#!/bin/bash
echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/00-docker
echo 'APT::Install-Recommends "0";' >> /etc/apt/apt.conf.d/00-docker
DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3  vim xinetd iputils-ping nmap wget\
  && rm -rf /var/lib/apt/lists/*


# Install step cli and step ca
wget https://dl.step.sm/gh-release/cli/docs-cli-install/v0.23.1/step-cli_0.23.1_amd64.deb --no-check-certificate
dpkg -i step-cli_0.23.1_amd64.deb
wget https://dl.step.sm/gh-release/certificates/docs-ca-install/v0.23.1/step-ca_0.23.1_amd64.deb --no-check-certificate
dpkg -i step-ca_0.23.1_amd64.deb

# create the CA

step certificate create --profile root-ca "THANOS Root CA" /home/step/root_ca.crt /home/step/root_ca.key --san=localhost --san=klapp-0130 --san=127.0.1.1/24 --san=10.202.0.52/24 --san=172.31.0.1/24 --password-file=/home/step/pw 

#--not-before=87660h

# create the intermediate CA

step certificate create "THANOS Intermediate CA 1"     /home/step/intermediate_ca.crt /home/step/intermediate_ca.key     --profile intermediate-ca --ca /home/step/root_ca.crt --ca-key /home/step/root_ca.key --ca-password-file=/home/step/pw --password-file=/home/step/pw


# create the certificate

step certificate create klapp-0130 /home/step/klapp-0130.crt /home/step/klapp-0130.key  --profile leaf --not-after=87660h  --ca /home/step/intermediate_ca.crt --ca-key /home/step/intermediate_ca.key --bundle --san=localhost --san=klapp-0130 --san=127.0.1.1/24 --san=10.202.0.52/2 --san=172.31.0.1/24 --password-file=home/step/pw --ca-password-file=/home/step/pw

#step ca init --deployment-type=standalone --name=thanos --dns=$(hostname -f) --address=:9443 --provisioner=thanos --password-file=/home/step/pw


#start the CA

#step-ca $(step path)/config/ca.json --password-file=/home/step/pw


##update the provisioner

#step ca provisioner update thanos    --x509-min-dur=20m    --x509-max-dur=87660h    --x509-default-dur=87660h

##

while true; do
  sleep 10000
done


