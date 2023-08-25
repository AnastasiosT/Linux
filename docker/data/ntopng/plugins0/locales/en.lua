-- Persistent Data
local multiRefObjects = {

} -- multiRefObjects
local obj1 = {
	["pool_connection_disconnection"] = {
		["description"] = "Trigger an alert when a host pool connects to - or disconnects from - the network.";
		["title"] = "Host Pool Connection/Disconnection";
	};
	["unexpected_smtp"] = {
		["unexpected_smtp_title"] = "Unexpected SMTP server";
		["description"] = "Comma separated values of SMTP servers IPs. Example: 173.194.76.109,52.97.232.242";
		["title"] = "Allowed SMTP servers";
		["unexpected_smtp_description"] = "Trigger an alert when not allowed SMTP server is detected";
		["alert_unexpected_smtp_title"] = "Unexpected SMTP server found";
		["status_unexpected_smtp_description"] = "Unexpected SMTP server found: %{server}";
	};
	["active_monitoring"] = {
		["cont_icmp"] = "Continuous ICMPv4";
		["24h"] = "24H Availability";
		["cont_icmp6"] = "Continuous ICMPv6";
	};
	["low_goodput"] = {
		["description"] = "Trigger alerts when flow goodput is too low (&lt;= 60%)";
		["title"] = "Low Goodput";
	};
	["unexpected_dhcp"] = {
		["unexpected_dhcp_description"] = "Trigger an alert when not allowed DHCP server is detected";
		["description"] = "Comma separated values of allowed DHCP IPs. Example: 192.168.1.1";
		["title"] = "Allowed DHCP";
		["alert_unexpected_dhcp_title"] = "Unexpected DHCP found";
		["status_unexpected_dhcp_description"] = "Unexpected DHCP server found: %{server}";
		["unexpected_dhcp_title"] = "Unexpected DHCP";
	};
	["unexpected_new_device"] = {
		["unexpected_new_device_title"] = "Unexpected Device Connected";
		["description"] = "Comma separated values of allowed MAC Addresses. Example: FF:FF:FF:FF:FF:FF";
		["status_unexpected_new_device_description"] = "Unexpected MAC address device <a href=\"%{host_url}\">%{mac_address}</a> connected to the network.";
		["unexpected_new_device_description"] = "Trigger an alert first time an unexpected (i.e. not part of the allowed MAC addresses list) device connects to the network.";
		["alert_unexpected_new_device_title"] = "Unexpected Device Connected";
		["status_unexpected_new_device_description_pro"] = "Unexpected MAC address device <a href=\"%{host_url}\">%{mac_address}</a> connected to the network. SNMP Device <a href=\"%{ip_url}\">%{ip}</a> on Port <a href=\"%{port_url}\">%{port}</a> <span class='badge badge-secondary'>%{interface_name}</span>";
		["title"] = "Allowed MAC Addresses";
	};
	["shell_alert_endpoint"] = {
		["shell_send_error"] = "Error while trying to run the script.";
		["shell_script"] = "Script PATH";
		["validation"] = {
			["invalid_script"] = "Invalid script. Script not secure.";
			["invalid_path"] = "Invalid shell script path. The script must be stored in \"/usr/share/ntopng/scripts/shell/\" and end with .sh.";
			["empty_path"] = "Shell script path cannot be empty.";
		};
		["shell_options"] = "Options";
		["shell_description"] = {
			["option_description"] = "Instructions<ul><li>Insert here the options you want to pass to the script</ul>";
			["path_description"] = "Note:<ul><li>The script must be stored in \"/usr/share/ntopng/scripts/shell/\"<li>The script options alert.* are expanded at runtime with the alert values</lu>";
		};
	};
	["ip_reassignment"] = {
		["description"] = "Trigger alerts when an IP address, previously seen with a MAC address, is now seen with another MAC address. This alert might indicate an ARP spoof attempt. Only works for the builtin alert recipient.";
		["title"] = "IP Reassignment";
	};
	["no_if_activity"] = {
		["no_if_activity_description"] = "Trigger an alert when no activity from an interface is detected";
		["no_if_activity_title"] = "No activity on interface";
		["status_no_activity_description"] = "No activity reported on network interface.";
		["alert_no_activity_title"] = "No activity on interface";
	};
	["new_api_demo"] = {
		["alert_host_new_api_demo_description"] = "%{host}: one_param = %{one_param} another_param = %{another_param}";
		["my_manifest_title"] = "My Manifest Title";
	};
	["pool_quota_exceeded"] = {
		["description"] = "Trigger an alert when a time/traffic quota is exceeded.";
		["title"] = "Quota Exceeded";
	};
	["unexpected_dns"] = {
		["unexpected_dns_title"] = "Unexpected DNS";
		["description"] = "Comma separated values of allowed DNS IPs. Example: 8.8.8.8,8.8.4.4,1.1.1.1";
		["unexpected_dns_description"] = "Trigger an alert when not allowed DNS server is detected";
		["title"] = "Allowed DNS";
		["alert_unexpected_dns_title"] = "Unexpected DNS found";
		["status_unexpected_dns_description"] = "Unexpected DNS server found: %{server}";
	};
	["remote_to_remote"] = {
		["description"] = "Trigger alerts for remote client hosts on remote-to-remote flows. Only works for the builtin alert recipient.";
		["title"] = "Remote to Remote Hosts";
	};
	["host_log_collector"] = {
		["title"] = "Host Log";
		["description"] = "Collect syslog logs from hosts and trigger alerts according to the configured severity level (0 for min verbosity, 7 for max)";
	};
	["syslog_alert_endpoint"] = {
		["host"] = "Host";
		["text"] = "Text";
		["description"] = "Host, Port and Protocol should be specified for remote syslog servers only.";
		["protocol"] = "Protocol";
		["alert_format"] = "Format";
		["validation"] = {
			["invalid_host"] = "Invalid Syslog host.";
			["invalid_port"] = "Invalid Syslog port.";
		};
		["content"] = "Content";
		["port"] = "Port";
	};
	["zero_tcp_window"] = {
		["status_zero_tcp_window_description_c2s"] = "Reported client TCP zero window";
		["status_zero_tcp_window_description"] = "Reported TCP Zero Window";
		["zero_tcp_window_title"] = "Zero TCP Window";
		["zero_tcp_window_description"] = "Trigger an alert when a flow TCP window is zero";
		["alert_zero_tcp_window_title"] = "TCP Zero Window";
		["alert_zero_tcp_window_description"] = "Reported TCP Zero Window";
		["status_zero_tcp_window_description_s2c"] = "Reported server TCP zero window ";
	};
	["discord_alert_endpoint"] = {
		["discord_send_error"] = "Error sending message to Discord.";
		["webhook_description"] = "Instructions:<ul><li>Open the Discord channel you want to receive ntopng notifications from.<li>From the channel menu, select Edit channel (or click on the wheel icon). <li>Click on Webhooks menu item.<li>Click the Create Webhook button and fill in the name of the bot that will post the messages (note that you can set it on the ntopng recipients page)<li>Note the URL from the WebHook URL field to be copied in the field above. <li>Click the Save button.</ul>";
		["message_sender"] = "Nickname of the discord message sender (optional). ";
		["validation"] = {
			["empty_url"] = "Discord Webook URL cannot be empty.";
			["invalid_username"] = "Invalid Discord username.";
			["invalid_url"] = "Invalid Discord Webhook URL. See https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks.";
		};
		["url"] = "WebHook URL";
		["username"] = "Username";
	};
	["telegram_alert_endpoint"] = {
		["telegram_token"] = "Token";
		["telegram_send_error"] = "Error sending message to Telegram.";
		["validation"] = {
			["invalid_channel_name"] = "Invalid Telegram Channel Name.";
			["invalid_token"] = "Invalid Telegram Token.";
		};
		["telegram_channel"] = "Channel Id";
		["webhook_description"] = {
			["token_description"] = "Instructions:<ul><li>Start a new chat with @BotFather<li>Type and send '/newbot'<li>Give a name to your bot<li>Give a username to your bot<li>Copy here the token the @BotFather gave to you</ul>";
			["channel_id_description"] = "Instructions if you want to use the bot in a group:<ul><li>Add to your group the bot you created<li>Add to your group @getidsbot<li>Copy here the id the @getidsbot gave to you</ul>Instructions if you want to use the bot in a chat:<ul><li>Start a new conversation with @getidsbot<li>Copy here the id the @getidsbot gave to you</ul>";
		};
	};
	["suricata_collector"] = {
		["title"] = "Suricata";
		["description"] = "Collect alerts and metadata from Suricata";
		["statistics"] = "Suricata Statistics";
	};
	["unexpected_ntp"] = {
		["unexpected_ntp_description"] = "Trigger an alert when not allowed NTP server is detected";
		["description"] = "Comma separated values of NTP servers IPs. Example: 173.194.76.109,52.97.232.242";
		["status_unexpected_ntp_description"] = "Unexpected NTP server found: %{server}";
		["unexpected_ntp_title"] = "Unexpected NTP server";
		["alert_unexpected_ntp_title"] = "Unexpected NTP server found";
		["title"] = "Allowed NTP servers";
	};
}
return obj1
