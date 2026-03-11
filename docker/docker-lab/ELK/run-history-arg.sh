#!/usr/bin/env bash

# logstash version
/usr/share/logstash/bin/logstash -V

# this is used in the logstash config
export basedir=$PWD

# writable tmp dir needed for logstash
mkdir -p $basedir/path.data

# run logstash, this is expensive and takes ~ 20seconds
# due to the --config.reload.automatic you can modify the config on the fly
# while keeping logstash running.
/usr/share/logstash/bin/logstash \
	--path.config $basedir/$1 \
	--path.data $basedir/path.data/ \
	--log.level=info \
	--config.reload.automatic
