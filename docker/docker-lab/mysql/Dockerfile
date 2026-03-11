FROM ubuntu:latest

RUN echo 'APT::Install-Suggests "0";' >> /etc/apt/apt.conf.d/00-docker
RUN echo 'APT::Install-Recommends "0";' >> /etc/apt/apt.conf.d/00-docker
RUN DEBIAN_FRONTEND=noninteractive \
  apt-get update \
  && apt-get install -y python3  vim xinetd iputils-ping nmap mysql-server mysql-client\
  && rm -rf /var/lib/apt/lists/*


RUN sed -i -e 's/127.0.0.1/0.0.0.0/' /etc/mysql/my.cnf

RUN usermod -d /var/lib/mysql/ mysql


COPY ./mysql.sh /usr/local/bin/mysql.sh

RUN ["chmod", "+x", "/usr/local/bin/mysql.sh"]


COPY check-mk-agent_2.1.0p14_all.deb /tmp

RUN dpkg -i /tmp/check-mk-agent_2.1.0p14_all.deb

CMD ["mysql.sh"]


EXPOSE 8080
