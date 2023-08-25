#!/bin/bash
echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/00-docker
echo 'APT::Install-Recommends "0";' >> /etc/apt/apt.conf.d/00-docker
DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3  vim xinetd iputils-ping nmap mysql-server mysql-client\
  && rm -rf /var/lib/apt/lists/*


## Configure mysql 
sed -i -e 's/127.0.0.1/0.0.0.0/' /etc/mysql/my.cnf
usermod -d /var/lib/mysql/ mysql
chmod +x /usr/local/bin/mysql.sh


##
## Insall the checkmk agent
dpkg -i /tmp/check-mk-agent_2.1.0p14_all.deb
##


service mysql restart

# Configure the mysql plugin for checkmk 
cp /tmp/mk_mysql /usr/lib/check_mk_agent/plugins/mk_mysql
chmod +x /usr/lib/check_mk_agent/plugins/mk_mysql
chmod 400 /etc/check_mk/mysql.cfg

mysql -e "CREATE USER 'checkmk'@'localhost' IDENTIFIED BY 'Cmkmyql';"
mysql -e "GRANT SELECT, SHOW DATABASES ON *.* TO 'checkmk'@'localhost';"
mysql -e "GRANT REPLICATION CLIENT ON *.* TO 'checkmk'@'localhost';"
##

while true; do
  sleep 10000
done


