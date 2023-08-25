-- Persistent Data
local multiRefObjects = {

} -- multiRefObjects
local obj1 = {
	["no_if_activity"] = {
		["no_if_activity_description"] = "Attiva un'allerta quando è riscontrata nessuna attività da parte di un'interfaccia di rete";
		["no_if_activity_title"] = "Nessuna attività da un'interfaccia";
		["status_no_activity_description"] = "Nessuna attività riportata dall'interfaccia di rete.";
		["alert_no_activity_title"] = "Nessuna attività dall'interfaccia";
	};
	["telegram_alert_endpoint"] = {
		["telegram_token"] = "Token";
		["telegram_send_error"] = "Errore nell'invio del messaggio a Telegram.";
		["validation"] = {
			["invalid_channel_name"] = "Nome del canale non valido.";
			["invalid_token"] = "Token di Telegram non valido.";
		};
		["telegram_channel"] = "Channel Id";
		["webhook_description"] = {
			["token_description"] = "Istruzioni:<ul><li>Inizia una nuova chat con @BotFather<li>Scrivi nella chat '/newbot'<li>Dai un nome al tuo bot<li>Dai uno username al tuo bot<li>Copia qui il token che @BotFather ti ha fornito</ul>";
			["channel_id_description"] = "Istruzioni se vuoi utilizzare il bot in un gruppo:<ul><li>Aggiungi al tuo gruppo il bot che hai creato<li>Aggiungi al tuo gruppo @getidsbot<li>Copia qui l'id che @getidsbot ti ha fornito</ul>Istruzioni se vuoi utilizzare il bot in una chat:<ul><li>Inizia una nuova chat con @getidsbot<li>Copia qui l'id che @getidsbot ti ha fornito</ul>";
		};
	};
	["shell_alert_endpoint"] = {
		["shell_send_error"] = "Errore nell'esecuzione dello script.";
		["shell_script"] = "Percorso (path) dello Script";
		["validation"] = {
			["invalid_script"] = "Script non valido. Script ritenuto non sicuro.";
			["invalid_path"] = "Percorso dello script shell non valido. Lo script deve essere nella cartella \"/usr/share/ntopng/scripts/shell/\" e deve avere il suffisso .sh.";
			["empty_path"] = "Il percorso di uno script shell non può essere vuoto.";
		};
		["shell_options"] = "Opzioni";
		["shell_description"] = {
			["option_description"] = "Istruzioni<ul><li>Inserire qui le opzioni che si vogliono passare allo script</ul>";
			["path_description"] = "Note:<ul><li>Lo script deve essere contenuto in \"/usr/share/ntopng/scripts/shell/\"<li>Le opzioni dello script alert.* saranno espanse a runtime con il valore dell'allarme</lu>";
		};
	};
	["zero_tcp_window"] = {
		["status_zero_tcp_window_description_c2s"] = "La TCP window del client è zero";
		["status_zero_tcp_window_description"] = "La TCP window è zero";
		["zero_tcp_window_title"] = "TCP Window Zero";
		["zero_tcp_window_description"] = "Emette un allarme quando la TCP window di un flusso ha dimensione zero";
		["alert_zero_tcp_window_title"] = "TCP Window Zero";
		["alert_zero_tcp_window_description"] = "La TCP Window è Zero";
		["status_zero_tcp_window_description_s2c"] = "La TCP window del server è zero";
	};
}
return obj1
