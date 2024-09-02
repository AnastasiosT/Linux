#!/bin/bash
HOSTNAME="abc"
timeout="60s"
dirs=()

# collect log entries of the host got scheduled
#stdbuf --output=0 tail -f  ~/var/log/cmc.log |grep --line-buffered '\[service "'$HOSTNAME';Check_MK"\].*sending request for host "'$HOSTNAME'"' >>~/special_agent.log
# collect timestamps of ~/tmp files

#tail -f ~/var/log/cmc.log | grep 'sending request for host "' >> ~/special_agent.log &
#timeout --foreground $timeout watch -g -n1 ls -ltr "./tmp/check_mk/data_source_cache/push-agent/$HOSTNAME >> ~/cachefile.txt" 


for i in $(find  -type d -name "abc"); do

        outcome_dirs+=($i)
done

echo ${outcome_dirs[@]}


for dir in "${outcome_dirs[@]}"; do
        timeout $timeout watch -g -n1  ls -ltr "$dir >>$dir.txt" &
done

wait

