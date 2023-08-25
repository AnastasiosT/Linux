#!/bin/bash -e
#docker run --net bridge --name ldap-service --volume /home/anastasios/Docker/docker-compose.yaml:/container/environment/01-custom/env.yaml --detach osixia/openldap:1.1.8
#docker run --net bridge --name ldap-service --env-file docker-compose.yaml --volume /home/anastasios/Docker/cmk.ldif:/tmp/ldif --cmd "cp -a /tmp/ldif/. /container/service/slapd/assets/config/bootstrap/ldif/50-bootstrap.ldif"  osixia/openldap:1.1.8 --copy-service 

docker run --net bridge --name ldap-service --env-file env.yaml -v /home/anastasios/Docker/org.ldif:/tmp/ldif --detach osixia/openldap:latest --cmd "cp -a /tmp/ldif /container/service/slapd/assets/config/bootstrap/ldif/50-bootstrap.ldif" 


docker run --name phpldapadmin-service --hostname phpldapadmin-service --link ldap-service:localhost --env PHPLDAPADMIN_LDAP_HOSTS=localhost --detach osixia/phpldapadmin:0.9.0




PHPLDAP_IP=$(docker inspect -f "{{ .NetworkSettings.IPAddress }}" phpldapadmin-service)
#PHPLDAP_IP=$(docker inspect -f "192.168.2.3" phpldapadmin-service)


echo "Go to: http://$PHPLDAP_IP"
Login=`cat docker-compose.yaml|grep BASE |awk '{print $2}'`
PWD=`cat docker-compose.yaml|grep ADMIN |awk '{print $2}'`
IPLDAP=`docker inspect -f '{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}' ldap-service`

echo $Login
echo $PWD
echo "LDAP-Service IP $IPLDAP"


