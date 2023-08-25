FROM osixia/openldap:latest
LABEL maintainer="thanos"
#ENV LDAP_ORGANISATION="CMK" 
#ENV LDAP_DOMAIN="cmk.dev.de"
Add environment /container/environment/01-custom
COPY org.ldif /container/service/slapd/assets/config/bootstrap/ldif/50-bootstrap.ldif

# Comment
RUN echo 'we are running some # of cool things'


RUN   apt clean && apt autoclean \
      && apt-get update && apt -y install vim iputils-ping nmap
