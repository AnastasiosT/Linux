-- Persistent Data
local multiRefObjects = {
{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};{};
} -- multiRefObjects
multiRefObjects[18]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/slow_purge";
multiRefObjects[18]["description"] = "Detects problems in hash tables purging";
multiRefObjects[18]["dependencies"] = {
};
multiRefObjects[18]["title"] = "Slow Purge";
multiRefObjects[18]["edition"] = "community";
multiRefObjects[18]["author"] = "ntop";
multiRefObjects[18]["key"] = "slow_purge";
multiRefObjects[24]["path"] = "/usr/share/ntopng/scripts/plugins/collectors/suricata_collector";
multiRefObjects[24]["description"] = "Collects events and alerts from suricata";
multiRefObjects[24]["dependencies"] = {
};
multiRefObjects[24]["title"] = "Suricata Collector";
multiRefObjects[24]["edition"] = "community";
multiRefObjects[24]["author"] = "ntop";
multiRefObjects[24]["key"] = "suricata_collector";
multiRefObjects[30]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/blacklisted_country";
multiRefObjects[30]["description"] = "Detects hosts contacts with specific countries";
multiRefObjects[30]["dependencies"] = {
};
multiRefObjects[30]["title"] = "Country Check";
multiRefObjects[30]["edition"] = "community";
multiRefObjects[30]["author"] = "ntop";
multiRefObjects[30]["key"] = "blacklisted_country";
multiRefObjects[20]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/device_application_not_allowed";
multiRefObjects[20]["description"] = "Detects applications not allowed for a specific device type and triggers alerts";
multiRefObjects[20]["dependencies"] = {
};
multiRefObjects[20]["title"] = "Device Application Not Allowed";
multiRefObjects[20]["edition"] = "community";
multiRefObjects[20]["author"] = "ntop";
multiRefObjects[20]["key"] = "device_application_not_allowed";
multiRefObjects[31]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/udp_unidirectional";
multiRefObjects[31]["description"] = "Detects UDP unidirectional flows";
multiRefObjects[31]["dependencies"] = {
};
multiRefObjects[31]["title"] = "UDP Unidirectional";
multiRefObjects[31]["edition"] = "community";
multiRefObjects[31]["author"] = "ntop";
multiRefObjects[31]["key"] = "udp_unidirectional";
multiRefObjects[13]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_new_device";
multiRefObjects[13]["description"] = "Trigger an alert when an unexpected device connects to the network.";
multiRefObjects[13]["dependencies"] = {
};
multiRefObjects[13]["title"] = "Unexpected Device Connected";
multiRefObjects[13]["edition"] = "community";
multiRefObjects[13]["author"] = "ntop";
multiRefObjects[13]["key"] = "unexpected_new_device";
multiRefObjects[21]["path"] = "/usr/share/ntopng/scripts/plugins/collectors/host_log_collector";
multiRefObjects[21]["description"] = "Collects syslog events from hosts";
multiRefObjects[21]["dependencies"] = {
};
multiRefObjects[21]["title"] = "Host Log Collector";
multiRefObjects[21]["edition"] = "community";
multiRefObjects[21]["author"] = "ntop";
multiRefObjects[21]["key"] = "host_log_collector";
multiRefObjects[43]["path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/disk_monitor";
multiRefObjects[43]["description"] = "Monitors storage free space";
multiRefObjects[43]["dependencies"] = {
};
multiRefObjects[43]["title"] = "Disk Monitor";
multiRefObjects[43]["edition"] = "community";
multiRefObjects[43]["author"] = "ntop";
multiRefObjects[43]["key"] = "disk_monitor";
multiRefObjects[8]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/flow_flood";
multiRefObjects[8]["description"] = "Detects flow flood attacks and triggers alerts";
multiRefObjects[8]["dependencies"] = {
};
multiRefObjects[8]["title"] = "Flow Flood detector";
multiRefObjects[8]["edition"] = "community";
multiRefObjects[8]["author"] = "ntop";
multiRefObjects[8]["key"] = "flow_flood";
multiRefObjects[22]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_ntp";
multiRefObjects[22]["description"] = "Trigger an alert when not allowed NTP server is detected";
multiRefObjects[22]["dependencies"] = {
};
multiRefObjects[22]["title"] = "Unexpected NTP server";
multiRefObjects[22]["edition"] = "community";
multiRefObjects[22]["author"] = "ntop";
multiRefObjects[22]["key"] = "unexpected_ntp";
multiRefObjects[2]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross";
multiRefObjects[2]["description"] = "Multiple threshold cross alerts";
multiRefObjects[2]["dependencies"] = {
};
multiRefObjects[2]["title"] = "Threshold Cross";
multiRefObjects[2]["edition"] = "community";
multiRefObjects[2]["author"] = "ntop";
multiRefObjects[2]["key"] = "threshold_cross";
multiRefObjects[11]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/not_purged";
multiRefObjects[11]["description"] = "Detect issues in purging idle flows from the flows hash table";
multiRefObjects[11]["dependencies"] = {
};
multiRefObjects[11]["title"] = "Not Purged";
multiRefObjects[11]["edition"] = "community";
multiRefObjects[11]["author"] = "ntop";
multiRefObjects[11]["key"] = "not_purged";
multiRefObjects[19]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/system/too_many_drops";
multiRefObjects[19]["description"] = "Detects excessive packet drops in network interfaces";
multiRefObjects[19]["dependencies"] = {
};
multiRefObjects[19]["title"] = "Too Many Drops";
multiRefObjects[19]["edition"] = "community";
multiRefObjects[19]["author"] = "ntop";
multiRefObjects[19]["key"] = "too_many_drops";
multiRefObjects[42]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/blacklisted";
multiRefObjects[42]["description"] = "Detects blacklisted hosts and triggers alerts";
multiRefObjects[42]["dependencies"] = {
};
multiRefObjects[42]["title"] = "Blacklisted Hosts";
multiRefObjects[42]["edition"] = "community";
multiRefObjects[42]["author"] = "ntop";
multiRefObjects[42]["key"] = "blacklisted";
multiRefObjects[15]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/system/external_alert_check";
multiRefObjects[15]["description"] = "Retrieves and triggers alerts from external sources (e.g. suricata)";
multiRefObjects[15]["dependencies"] = {
};
multiRefObjects[15]["title"] = "External Alert";
multiRefObjects[15]["edition"] = "community";
multiRefObjects[15]["author"] = "ntop";
multiRefObjects[15]["key"] = "external_alert_check";
multiRefObjects[1]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/flow_calls_drops";
multiRefObjects[1]["description"] = "Detects drops in flow user scripts calls and triggers alerts";
multiRefObjects[1]["dependencies"] = {
};
multiRefObjects[1]["title"] = "Flow Calls Drops";
multiRefObjects[1]["edition"] = "community";
multiRefObjects[1]["author"] = "ntop";
multiRefObjects[1]["key"] = "flow_calls_drops";
multiRefObjects[3]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/alerts_drops";
multiRefObjects[3]["description"] = "Triggers an alert on the system when any interface has dropped alerts";
multiRefObjects[3]["dependencies"] = {
};
multiRefObjects[3]["title"] = "Dropped Alerts";
multiRefObjects[3]["edition"] = "community";
multiRefObjects[3]["author"] = "ntop";
multiRefObjects[3]["key"] = "alerts_drops";
multiRefObjects[7]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/new_api_demo";
multiRefObjects[7]["description"] = "Demo plugin to trigger flow alerts with the new API";
multiRefObjects[7]["dependencies"] = {
};
multiRefObjects[7]["title"] = "Demo to trigger flow alerts with the new API";
multiRefObjects[7]["edition"] = "community";
multiRefObjects[7]["author"] = "ntop";
multiRefObjects[7]["key"] = "new_api_demo";
multiRefObjects[25]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_dhcp";
multiRefObjects[25]["description"] = "Trigger an alert when an unexpected DHCP server is detected";
multiRefObjects[25]["dependencies"] = {
};
multiRefObjects[25]["title"] = "Unexpected DHCP";
multiRefObjects[25]["edition"] = "community";
multiRefObjects[25]["author"] = "Daniele Zulberti, Luca Argentieri";
multiRefObjects[25]["key"] = "unexpected_dhcp";
multiRefObjects[27]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/syn_flood";
multiRefObjects[27]["description"] = "Detects TCP SYN flood attacks on hosts and triggers alerts";
multiRefObjects[27]["dependencies"] = {
};
multiRefObjects[27]["title"] = "TCP SYN Flood detector";
multiRefObjects[27]["edition"] = "community";
multiRefObjects[27]["author"] = "ntop";
multiRefObjects[27]["key"] = "syn_flood";
multiRefObjects[23]["path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/influxdb_monitor";
multiRefObjects[23]["description"] = "Monitors the status of InfluxDB";
multiRefObjects[23]["dependencies"] = {
};
multiRefObjects[23]["title"] = "InluxDB Monitor";
multiRefObjects[23]["edition"] = "community";
multiRefObjects[23]["author"] = "ntop";
multiRefObjects[23]["key"] = "influxdb_monitor";
multiRefObjects[26]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_smtp";
multiRefObjects[26]["description"] = "Trigger an alert when not allowed SMTP server is detected";
multiRefObjects[26]["dependencies"] = {
};
multiRefObjects[26]["title"] = "Unexpected SMTP server";
multiRefObjects[26]["edition"] = "community";
multiRefObjects[26]["author"] = "Daniele Zulberti, Luca Argentieri";
multiRefObjects[26]["key"] = "unexpected_smtp";
multiRefObjects[9]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/zero_tcp_window";
multiRefObjects[9]["description"] = "Detects if there a flow TCP window value is zero, if it is triggers an alert";
multiRefObjects[9]["dependencies"] = {
};
multiRefObjects[9]["title"] = "Zero TCP Window check";
multiRefObjects[9]["edition"] = "community";
multiRefObjects[9]["author"] = "ntop";
multiRefObjects[9]["key"] = "zero_tcp_window";
multiRefObjects[36]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/snmp_topology_change";
multiRefObjects[36]["description"] = "Detects changes in the SNMP network topology and triggers alerts";
multiRefObjects[36]["dependencies"] = {
};
multiRefObjects[36]["title"] = "LLDP Topology Monitor";
multiRefObjects[36]["edition"] = "community";
multiRefObjects[36]["author"] = "ntop";
multiRefObjects[36]["key"] = "snmp_topology_change";
multiRefObjects[41]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/web_mining";
multiRefObjects[41]["description"] = "Detects web mining flows";
multiRefObjects[41]["dependencies"] = {
};
multiRefObjects[41]["title"] = "Web Mining";
multiRefObjects[41]["edition"] = "community";
multiRefObjects[41]["author"] = "ntop";
multiRefObjects[41]["key"] = "web_mining";
multiRefObjects[38]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/syn_scan_alert";
multiRefObjects[38]["description"] = "Detects SYN scan attacks on hosts and networks and triggers alerts";
multiRefObjects[38]["dependencies"] = {
};
multiRefObjects[38]["title"] = "SYN Scan detector";
multiRefObjects[38]["edition"] = "community";
multiRefObjects[38]["author"] = "ntop";
multiRefObjects[38]["key"] = "syn_scan_alert";
multiRefObjects[28]["path"] = "/usr/share/ntopng/scripts/plugins/examples/flow_logger";
multiRefObjects[28]["description"] = "Logs on the console each new flow";
multiRefObjects[28]["dependencies"] = {
};
multiRefObjects[28]["title"] = "Flow Logger";
multiRefObjects[28]["edition"] = "community";
multiRefObjects[28]["author"] = "ntop";
multiRefObjects[28]["key"] = "flow_logger";
multiRefObjects[39]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/low_goodput";
multiRefObjects[39]["description"] = "Detects flows with low goodput";
multiRefObjects[39]["dependencies"] = {
};
multiRefObjects[39]["title"] = "Low goodput";
multiRefObjects[39]["edition"] = "community";
multiRefObjects[39]["author"] = "ntop";
multiRefObjects[39]["key"] = "low_goodput";
multiRefObjects[40]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/request_reply_ratio";
multiRefObjects[40]["description"] = "Trigger alerts when on the requests/reply ratio";
multiRefObjects[40]["dependencies"] = {
};
multiRefObjects[40]["title"] = "Requests vs Replies Ratio";
multiRefObjects[40]["edition"] = "community";
multiRefObjects[40]["author"] = "ntop";
multiRefObjects[40]["key"] = "request_reply_ratio";
multiRefObjects[37]["path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/timeseries";
multiRefObjects[37]["description"] = "Contains scripts executed periodically to dump timeseries";
multiRefObjects[37]["dependencies"] = {
};
multiRefObjects[37]["title"] = "Timeseries";
multiRefObjects[37]["edition"] = "community";
multiRefObjects[37]["author"] = "ntop";
multiRefObjects[37]["key"] = "timeseries";
multiRefObjects[16]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/app_misconfiguration";
multiRefObjects[16]["description"] = "Detects problems in app configuration";
multiRefObjects[16]["dependencies"] = {
};
multiRefObjects[16]["title"] = "App Misconfiguration";
multiRefObjects[16]["edition"] = "community";
multiRefObjects[16]["author"] = "ntop";
multiRefObjects[16]["key"] = "app_misconfiguration";
multiRefObjects[35]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/flow_risks";
multiRefObjects[35]["description"] = "Report flow risks detected by nDPI";
multiRefObjects[35]["dependencies"] = {
};
multiRefObjects[35]["title"] = "Flow Risks";
multiRefObjects[35]["edition"] = "community";
multiRefObjects[35]["author"] = "ntop";
multiRefObjects[35]["key"] = "flow_risks";
multiRefObjects[34]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/remote_to_remote";
multiRefObjects[34]["description"] = "Detects remote to remote flows and triggers alerts";
multiRefObjects[34]["dependencies"] = {
};
multiRefObjects[34]["title"] = "Remote to Remote";
multiRefObjects[34]["edition"] = "community";
multiRefObjects[34]["author"] = "ntop";
multiRefObjects[34]["key"] = "remote_to_remote";
multiRefObjects[33]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/pool_connection_disconnection";
multiRefObjects[33]["description"] = "Trigger an alert upon host pool connection/disconnection";
multiRefObjects[33]["dependencies"] = {
};
multiRefObjects[33]["title"] = "Host Pool Connection/Disconnection";
multiRefObjects[33]["edition"] = "community";
multiRefObjects[33]["author"] = "ntop";
multiRefObjects[33]["key"] = "pool_connection_disconnection";
multiRefObjects[32]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/tcp_connection_issues";
multiRefObjects[32]["description"] = "Detects TCP Connection Issues";
multiRefObjects[32]["dependencies"] = {
};
multiRefObjects[32]["title"] = "TCP Connection Issues";
multiRefObjects[32]["edition"] = "community";
multiRefObjects[32]["author"] = "ntop";
multiRefObjects[32]["key"] = "tcp_connection_issues";
multiRefObjects[12]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_dns";
multiRefObjects[12]["description"] = "Trigger an alert when an unexpected DNS server is detected";
multiRefObjects[12]["dependencies"] = {
};
multiRefObjects[12]["title"] = "Unexpected DNS";
multiRefObjects[12]["edition"] = "community";
multiRefObjects[12]["author"] = "Daniele Zulberti, Luca Argentieri";
multiRefObjects[12]["key"] = "unexpected_dns";
multiRefObjects[5]["path"] = "/usr/share/ntopng/scripts/plugins/monitors/network/active_monitoring";
multiRefObjects[5]["edition"] = "community";
multiRefObjects[5]["description"] = "Monitors the status and the response time of specific hosts";
multiRefObjects[5]["dependencies"] = {
};
multiRefObjects[5]["title"] = "Active Monitoring";
multiRefObjects[5]["key"] = "active_monitoring";
multiRefObjects[5]["author"] = "ntop";
multiRefObjects[5]["data_dirs"] = {
	[1] = "measurements";
};
multiRefObjects[17]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/pool_quota_exceeded";
multiRefObjects[17]["description"] = "Trigger an alert when a time/traffic quota is exceeded";
multiRefObjects[17]["dependencies"] = {
};
multiRefObjects[17]["title"] = "Quota Exceeded";
multiRefObjects[17]["edition"] = "community";
multiRefObjects[17]["author"] = "ntop";
multiRefObjects[17]["key"] = "pool_quota_exceeded";
multiRefObjects[14]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/periodic_activities";
multiRefObjects[14]["description"] = "Checks the state and functioning of periodic activities";
multiRefObjects[14]["dependencies"] = {
};
multiRefObjects[14]["title"] = "Periodic Activities";
multiRefObjects[14]["edition"] = "community";
multiRefObjects[14]["author"] = "ntop";
multiRefObjects[14]["key"] = "periodic_activities";
multiRefObjects[29]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/ip_reassignment";
multiRefObjects[29]["description"] = "Detects remote to remote flows and triggers alerts";
multiRefObjects[29]["dependencies"] = {
};
multiRefObjects[29]["title"] = "Remote to Remote";
multiRefObjects[29]["edition"] = "community";
multiRefObjects[29]["author"] = "ntop";
multiRefObjects[29]["key"] = "ip_reassignment";
multiRefObjects[10]["path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/redis_monitor";
multiRefObjects[10]["description"] = "Monitors Redis health and performance";
multiRefObjects[10]["dependencies"] = {
};
multiRefObjects[10]["title"] = "Redis Monitor";
multiRefObjects[10]["edition"] = "community";
multiRefObjects[10]["author"] = "ntop";
multiRefObjects[10]["key"] = "redis_monitor";
multiRefObjects[6]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/ghost_networks";
multiRefObjects[6]["description"] = "Detects ghost networks and trigger alerts";
multiRefObjects[6]["dependencies"] = {
};
multiRefObjects[6]["title"] = "Ghost Networks";
multiRefObjects[6]["edition"] = "community";
multiRefObjects[6]["author"] = "ntop";
multiRefObjects[6]["key"] = "ghost_networks";
multiRefObjects[4]["path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/no_if_activity";
multiRefObjects[4]["description"] = "Detects if there is activity on a network interface, if not calls and triggers an alert";
multiRefObjects[4]["dependencies"] = {
};
multiRefObjects[4]["title"] = "Interface activity check";
multiRefObjects[4]["edition"] = "community";
multiRefObjects[4]["author"] = "ntop";
multiRefObjects[4]["key"] = "no_if_activity";
local obj1 = {
	["path_map"] = {
		["/var/lib/ntopng/plugins0/callbacks/system/system/remote_to_remote.lua"] = {
			["plugin"] = multiRefObjects[34];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/remote_to_remote/user_scripts/system/remote_to_remote.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/throughput.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/host/throughput.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/bytes.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/interface/bytes.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/periodic_activity_not_executed.lua"] = {
			["plugin"] = multiRefObjects[14];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/periodic_activities/user_scripts/system/periodic_activity_not_executed.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/alerts_ts.lua"] = {
			["plugin"] = multiRefObjects[37];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/timeseries/user_scripts/system/alerts_ts.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/flow_flood_victim.lua"] = {
			["plugin"] = multiRefObjects[8];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/flow_flood/user_scripts/host/flow_flood_victim.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/device_protocol_not_allowed.lua"] = {
			["plugin"] = multiRefObjects[20];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/device_application_not_allowed/user_scripts/flow/device_protocol_not_allowed.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/network/syn_scan_victim.lua"] = {
			["plugin"] = multiRefObjects[38];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/syn_scan_alert/user_scripts/network/syn_scan_victim.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/request_reply_ratio.lua"] = {
			["plugin"] = multiRefObjects[40];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/request_reply_ratio/user_scripts/host/request_reply_ratio.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/syn_scan_attacker.lua"] = {
			["plugin"] = multiRefObjects[38];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/syn_scan_alert/user_scripts/host/syn_scan_attacker.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/periodic_activity_not_executed.lua"] = {
			["plugin"] = multiRefObjects[14];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/periodic_activities/user_scripts/interface/periodic_activity_not_executed.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/low_goodput.lua"] = {
			["plugin"] = multiRefObjects[39];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/low_goodput/user_scripts/flow/low_goodput.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/syslog/suricata.lua"] = {
			["plugin"] = multiRefObjects[24];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/collectors/suricata_collector/user_scripts/syslog/suricata.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/unexpected_new_device.lua"] = {
			["plugin"] = multiRefObjects[13];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_new_device/user_scripts/interface/unexpected_new_device.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/idle.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/interface/idle.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/syslog/host_log.lua"] = {
			["plugin"] = multiRefObjects[21];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/collectors/host_log_collector/user_scripts/syslog/host_log.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/too_many_drops.lua"] = {
			["plugin"] = multiRefObjects[19];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/system/too_many_drops/user_scripts/interface/too_many_drops.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/dns.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/interface/dns.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/packets.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/host/packets.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/syn_scan_victim.lua"] = {
			["plugin"] = multiRefObjects[38];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/syn_scan_alert/user_scripts/host/syn_scan_victim.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/pool_connection_disconnection.lua"] = {
			["plugin"] = multiRefObjects[33];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/pool_connection_disconnection/user_scripts/interface/pool_connection_disconnection.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/tcp_issues_generic.lua"] = {
			["plugin"] = multiRefObjects[32];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/tcp_connection_issues/user_scripts/flow/tcp_issues_generic.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/idle.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/host/idle.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/web_mining.lua"] = {
			["plugin"] = multiRefObjects[41];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/web_mining/user_scripts/flow/web_mining.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/external_alert_check.lua"] = {
			["plugin"] = multiRefObjects[15];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/system/external_alert_check/user_scripts/flow/external_alert_check.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/network/flow_flood_victim.lua"] = {
			["plugin"] = multiRefObjects[8];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/flow_flood/user_scripts/network/flow_flood_victim.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/active.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/host/active.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/memory_ts.lua"] = {
			["plugin"] = multiRefObjects[37];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/timeseries/user_scripts/system/memory_ts.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/network/egress.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/network/egress.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/syn_flood_attacker.lua"] = {
			["plugin"] = multiRefObjects[27];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/syn_flood/user_scripts/host/syn_flood_attacker.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/blacklisted.lua"] = {
			["plugin"] = multiRefObjects[42];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/blacklisted/user_scripts/flow/blacklisted.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/network/syn_flood_victim.lua"] = {
			["plugin"] = multiRefObjects[27];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/syn_flood/user_scripts/network/syn_flood_victim.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/not_purged.lua"] = {
			["plugin"] = multiRefObjects[11];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/not_purged/user_scripts/flow/not_purged.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/disk_monitor.lua"] = {
			["plugin"] = multiRefObjects[43];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/disk_monitor/user_scripts/system/disk_monitor.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/country_check.lua"] = {
			["plugin"] = multiRefObjects[30];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/blacklisted_country/user_scripts/flow/country_check.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/flow_risks.lua"] = {
			["plugin"] = multiRefObjects[35];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/flow_risks/user_scripts/flow/flow_risks.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/flow_calls_drops.lua"] = {
			["plugin"] = multiRefObjects[1];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/flow_calls_drops/user_scripts/interface/flow_calls_drops.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/p2p.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/host/p2p.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/slow_periodic_activity.lua"] = {
			["plugin"] = multiRefObjects[14];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/periodic_activities/user_scripts/system/slow_periodic_activity.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/remote_to_remote.lua"] = {
			["plugin"] = multiRefObjects[34];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/remote_to_remote/user_scripts/flow/remote_to_remote.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/no_if_activity.lua"] = {
			["plugin"] = multiRefObjects[4];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/no_if_activity/user_scripts/interface/no_if_activity.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/dropped_alerts.lua"] = {
			["plugin"] = multiRefObjects[3];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/alerts_drops/user_scripts/interface/dropped_alerts.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/udp_unidirectional.lua"] = {
			["plugin"] = multiRefObjects[31];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/udp_unidirectional/user_scripts/flow/udp_unidirectional.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/packets.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/interface/packets.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/new_api_demo.lua"] = {
			["plugin"] = multiRefObjects[7];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/new_api_demo/user_scripts/host/new_api_demo.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/ip_reassignment.lua"] = {
			["plugin"] = multiRefObjects[29];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/ip_reassignment/user_scripts/system/ip_reassignment.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/snmp_device/lldp_topology_changed.lua"] = {
			["plugin"] = multiRefObjects[36];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/snmp_topology_change/user_scripts/snmp_device/lldp_topology_changed.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/zero_tcp_window.lua"] = {
			["plugin"] = multiRefObjects[9];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/zero_tcp_window/user_scripts/flow/zero_tcp_window.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/dns.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/host/dns.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/too_many_flows.lua"] = {
			["plugin"] = multiRefObjects[16];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/app_misconfiguration/user_scripts/interface/too_many_flows.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/pool_quota_exceeded.lua"] = {
			["plugin"] = multiRefObjects[17];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/pool_quota_exceeded/user_scripts/interface/pool_quota_exceeded.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/influxdb_monitor.lua"] = {
			["plugin"] = multiRefObjects[23];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/influxdb_monitor/user_scripts/system/influxdb_monitor.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/new_api_demo.lua"] = {
			["plugin"] = multiRefObjects[7];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/new_api_demo/user_scripts/flow/new_api_demo.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/flows.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/host/flows.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/slow_periodic_activity.lua"] = {
			["plugin"] = multiRefObjects[14];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/periodic_activities/user_scripts/interface/slow_periodic_activity.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/bytes.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/host/bytes.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/slow_purge.lua"] = {
			["plugin"] = multiRefObjects[18];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/slow_purge/user_scripts/interface/slow_purge.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/flow_logger.lua"] = {
			["plugin"] = multiRefObjects[28];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/examples/flow_logger/user_scripts/flow/flow_logger.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/network/ingress.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/network/ingress.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/throughput.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/interface/throughput.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/flow_flood_attacker.lua"] = {
			["plugin"] = multiRefObjects[8];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/flow_flood/user_scripts/host/flow_flood_attacker.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/too_many_hosts.lua"] = {
			["plugin"] = multiRefObjects[16];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/app_misconfiguration/user_scripts/interface/too_many_hosts.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/active_monitoring.lua"] = {
			["plugin"] = multiRefObjects[5];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/monitors/network/active_monitoring/user_scripts/system/active_monitoring.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/unexpected_dns.lua"] = {
			["plugin"] = multiRefObjects[12];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_dns/user_scripts/flow/unexpected_dns.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/unexpected_smtp.lua"] = {
			["plugin"] = multiRefObjects[26];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_smtp/user_scripts/flow/unexpected_smtp.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/unexpected_dhcp.lua"] = {
			["plugin"] = multiRefObjects[25];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_dhcp/user_scripts/flow/unexpected_dhcp.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/ghost_networks.lua"] = {
			["plugin"] = multiRefObjects[6];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/ghost_networks/user_scripts/interface/ghost_networks.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/redis_monitor.lua"] = {
			["plugin"] = multiRefObjects[10];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/monitors/system/redis_monitor/user_scripts/system/redis_monitor.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/active_local_hosts.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/interface/active_local_hosts.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/system/system/dropped_alerts.lua"] = {
			["plugin"] = multiRefObjects[3];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/internals/alerts_drops/user_scripts/system/dropped_alerts.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/interface/p2p.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/interface/p2p.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/host/syn_flood_victim.lua"] = {
			["plugin"] = multiRefObjects[27];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/syn_flood/user_scripts/host/syn_flood_victim.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/flow/unexpected_ntp.lua"] = {
			["plugin"] = multiRefObjects[22];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/security/unexpected_ntp/user_scripts/flow/unexpected_ntp.lua";
		};
		["/var/lib/ntopng/plugins0/callbacks/interface/network/inner.lua"] = {
			["plugin"] = multiRefObjects[2];
			["source_path"] = "/usr/share/ntopng/scripts/plugins/alerts/network/threshold_cross/user_scripts/network/inner.lua";
		};
	};
	["plugins"] = {
		["telegram_alert_endpoint"] = {
			["path"] = "/usr/share/ntopng/scripts/plugins/endpoints/telegram_alert_endpoint";
			["description"] = "Provides alerts notifications to telegram";
			["dependencies"] = {
			};
			["title"] = "Telegram Alert Endpoint";
			["edition"] = "community";
			["author"] = "ntop";
			["key"] = "telegram_alert_endpoint";
		};
		["ghost_networks"] = multiRefObjects[6];
		["unexpected_smtp"] = multiRefObjects[26];
		["app_misconfiguration"] = multiRefObjects[16];
		["active_monitoring"] = multiRefObjects[5];
		["slow_purge"] = multiRefObjects[18];
		["unexpected_dhcp"] = multiRefObjects[25];
		["web_mining"] = multiRefObjects[41];
		["udp_unidirectional"] = multiRefObjects[31];
		["shell_alert_endpoint"] = {
			["path"] = "/usr/share/ntopng/scripts/plugins/endpoints/shell_alert_endpoint";
			["description"] = "Provides shell script execution in case an alerts is triggered";
			["dependencies"] = {
			};
			["title"] = "Shell Script Alert Endpoint";
			["edition"] = "community";
			["author"] = "ntop";
			["key"] = "shell_alert_endpoint";
		};
		["syn_flood"] = multiRefObjects[27];
		["redis_monitor"] = multiRefObjects[10];
		["ip_reassignment"] = multiRefObjects[29];
		["sqlite_alert_endpoint"] = {
			["path"] = "/usr/share/ntopng/scripts/plugins/endpoints/sqlite_alert_endpoint";
			["description"] = "Handles SQLite alert notifications for the UI";
			["dependencies"] = {
			};
			["title"] = "SQLite Alert Endpoint";
			["edition"] = "community";
			["author"] = "ntop";
			["key"] = "sqlite_alert_endpoint";
		};
		["blacklisted_country"] = multiRefObjects[30];
		["remote_to_remote"] = multiRefObjects[34];
		["host_log_collector"] = multiRefObjects[21];
		["suricata_collector"] = multiRefObjects[24];
		["unexpected_ntp"] = multiRefObjects[22];
		["too_many_drops"] = multiRefObjects[19];
		["pool_connection_disconnection"] = multiRefObjects[33];
		["blacklisted"] = multiRefObjects[42];
		["no_if_activity"] = multiRefObjects[4];
		["not_purged"] = multiRefObjects[11];
		["syn_scan_alert"] = multiRefObjects[38];
		["periodic_activities"] = multiRefObjects[14];
		["device_application_not_allowed"] = multiRefObjects[20];
		["unexpected_new_device"] = multiRefObjects[13];
		["alerts_drops"] = multiRefObjects[3];
		["threshold_cross"] = multiRefObjects[2];
		["flow_flood"] = multiRefObjects[8];
		["zero_tcp_window"] = multiRefObjects[9];
		["slack_alert_endpoint"] = {
			["path"] = "/usr/share/ntopng/scripts/plugins/endpoints/slack_alert_endpoint";
			["description"] = "Provides alerts notifications to Slack";
			["dependencies"] = {
			};
			["title"] = "Slack Alert Endpoint";
			["edition"] = "community";
			["author"] = "ntop";
			["key"] = "slack_alert_endpoint";
		};
		["disk_monitor"] = multiRefObjects[43];
		["unexpected_dns"] = multiRefObjects[12];
		["request_reply_ratio"] = multiRefObjects[40];
		["flow_logger"] = multiRefObjects[28];
		["flow_calls_drops"] = multiRefObjects[1];
		["email_alert_endpoint"] = {
			["path"] = "/usr/share/ntopng/scripts/plugins/endpoints/email_alert_endpoint";
			["description"] = "Provides alerts notifications via emails";
			["dependencies"] = {
			};
			["title"] = "Email Alert Endpoint";
			["edition"] = "community";
			["author"] = "ntop";
			["key"] = "email_alert_endpoint";
		};
		["influxdb_monitor"] = multiRefObjects[23];
		["new_api_demo"] = multiRefObjects[7];
		["pool_quota_exceeded"] = multiRefObjects[17];
		["tcp_connection_issues"] = multiRefObjects[32];
		["discord_alert_endpoint"] = {
			["path"] = "/usr/share/ntopng/scripts/plugins/endpoints/discord_alert_endpoint";
			["description"] = "Provides alerts notifications to discord";
			["dependencies"] = {
			};
			["title"] = "Discords Alert Endpoint";
			["edition"] = "community";
			["author"] = "ntop";
			["key"] = "discord_alert_endpoint";
		};
		["low_goodput"] = multiRefObjects[39];
		["external_alert_check"] = multiRefObjects[15];
		["webhook_alert_endpoint"] = {
			["path"] = "/usr/share/ntopng/scripts/plugins/endpoints/webhook_alert_endpoint";
			["description"] = "Provides alerts notifications via webhooks";
			["dependencies"] = {
			};
			["title"] = "Webhook Alert Endpoint";
			["edition"] = "community";
			["author"] = "ntop";
			["key"] = "webhook_alert_endpoint";
		};
		["flow_risks"] = multiRefObjects[35];
		["snmp_topology_change"] = multiRefObjects[36];
		["syslog_alert_endpoint"] = {
			["path"] = "/usr/share/ntopng/scripts/plugins/endpoints/syslog_alert_endpoint";
			["description"] = "Provides alerts notifications to Syslog";
			["dependencies"] = {
			};
			["title"] = "Syslog Alert Endpoint";
			["edition"] = "community";
			["author"] = "ntop";
			["key"] = "syslog_alert_endpoint";
		};
		["timeseries"] = multiRefObjects[37];
	};
}
return obj1
