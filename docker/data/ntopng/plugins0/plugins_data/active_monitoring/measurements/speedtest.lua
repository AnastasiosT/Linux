--
-- (C) 2020 - ntop.org
--

--
-- This module implements an internet download bandwidth monitor.
--

local os_utils = require("os_utils")
local json = require("dkjson")
local ts_utils = require("ts_utils_core")

local do_trace = false
local collected_results = {}

-- #################################################################

-- The function called periodically to send the host probes.
-- hosts contains the list of hosts to probe, The table keys are
-- the hosts identifiers, whereas the table values contain host information
-- see (am_utils.key2host for the details on such format).
local function run_speedtest(hosts, granularity)
   local rsp = ntop.speedtest()

   if(not rsp) then
      return
   end

   if do_trace then
      tprint(hosts)
   end

   if do_trace then
      print(rsp)
   end

   rsp = json.decode(rsp)

   if(not rsp) then
      return
   end

   -- NOTE: force_host is set, only a single host will be available
   for key, host in pairs(hosts) do
      if(rsp["download.speed"] ~= nil) then
	 local isp = nil
	 local download_mbit = rsp["download.speed"]

	 if(type(rsp["client.isp"] == "string")) then
	    isp = noHtml(rsp["client.isp"])
	 end

	 collected_results[key] = {
	    value = download_mbit,
	    resolved_addr = isp,
	 }
      end

      if(rsp["upload.speed"]) then
	 ts_utils.append("am_host:upload_" .. granularity, {
	    ifid = getSystemInterfaceId(),
	    speed = rsp["upload.speed"] * 1000000,
	    host = host.host,
	 })
      end

      if(rsp["server.latency"]) then
	 ts_utils.append("am_host:latency_" .. granularity, {
	    ifid = getSystemInterfaceId(),
	    latency = rsp["server.latency"],
	    host = host.host,
	 })
      end
   end
end

-- #################################################################

-- The function responsible for collecting the results.
-- It must return a table containing a list of hosts along with their retrieved
-- measurement. The keys of the table are the host key. The values have the following format:
--  table
--	resolved_addr: (optional) the resolved IP address of the host
--	value: (optional) the measurement numeric value. If unspecified, the host is still considered unreachable.
local function collect_speedtest(granularity)
   return(collected_results)
end

-- #################################################################

return {
   -- Defines a list of measurements implemented by this script.
   -- The probing logic is implemented into the check() and collect_results().
   --
   -- Here is how the probing occurs:
   --	1. The check function is called with the list of hosts to probe. Ideally this
   --	   call should not block (e.g. should not wait for the results)
   --	2. The active_monitoring.lua code sleeps for some seconds
   --	3. The collect_results function is called. This should retrieve the results
   --       for the hosts checked in the check() function and return the results.
   --
   -- The alerts for non-responding hosts and the Active Monitoring timeseries are automatically
   -- generated by active_monitoring.lua . The timeseries are saved in the following schemas:
   -- "am_host:val_min", "am_host:val_5mins", "am_host:val_hour".
   measurements = {
      {
	 -- The unique key for the measurement
	 key = "speedtest",
	 -- The localization string for this measurement
	 i18n_label = "active_monitoring_stats.speedtest",
	 -- The function called periodically to send the host probes
	 check = run_speedtest,
	 -- The function responsible for collecting the results
	 collect_results = collect_speedtest,
	 -- The granularities allowed for the probe. See supported_granularities in active_monitoring.lua
	 granularities = { "5mins", "hour", "daily"},
	 -- The localization string for the measurement unit (e.g. "ms", "Mbits")
	 i18n_unit = "field_units.mbits",
	 -- The localization string for the Jitter unit (e.g. "ms", "Mbits")
	 i18n_jitter_unit = nil,
	 -- The localization string for the Active Monitoring timeseries menu entry
	 i18n_am_ts_label = "active_monitoring_stats.download_speed",
	 -- The localization string for the Active Monitoring metric in the chart
	 i18n_am_ts_metric = "active_monitoring_stats.download_speed",
	 -- The operator to use when comparing the measurement with the threshold, "gt" for ">" or "lt" for "<".
	 operator = "lt",
	 -- If set, indicates a maximum threshold value
	 max_threshold = 10000,
	 -- If set, indicates the default threshold value
	 default_threshold = nil,
	 -- A list of additional timeseries (the am_host:val_* is always shown) to show in the charts.
	 -- See https://www.ntop.org/guides/ntopng/api/timeseries/adding_new_timeseries.html#charting-new-metrics .
	 additional_timeseries = {{
	    schema="am_host:upload",
	    label=i18n("active_monitoring_stats.upload_speed"),
	    metrics_labels = { i18n("active_monitoring_stats.upload_speed"), },
	    value_formatter = {"NtopUtils.fbits", "NtopUtils.fbits"},
	    show_unreachable = true, -- Show the unreachable host status as a red line
	 }, {
	    schema="am_host:latency",
	    label=i18n("flow_details.round_trip_time"),
	    metrics_labels = { i18n("graphs.num_ms_rtt"), },
	    value_formatter = {"NtopUtils.fmillis", "NtopUtils.fmillis"},
	    show_unreachable = true, -- Show the unreachable host status as a red line
	 }},
	 -- Js function to call to format the measurement value. See ntopng_utils.js .
	 value_js_formatter = "NtopUtils.fbits",
	 -- The raw measurement value is multiplied by this factor before being written into the chart
	 chart_scaling_value = 1000000,
	 -- A list of additional notes (localization strings) to show into the timeseries charts
	 i18n_chart_notes = {},
	 -- If set, the user cannot change the host
	 force_host = "speedtest.net",
	 -- An alternative localization string for the unrachable alert message
	 unreachable_alert_i18n = "alert_messages.speedtest_failed",
      },
   },

   -- A setup function to possibly disable the plugin
   setup = check_binary,
}