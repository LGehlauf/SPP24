# SPP24
Notes für Jasper und Leo
- FLF = Fertigungs-Log-Files, TLF = Transport-Log-Files
- Ich empfehle, dass ihr euch für eure Zwecke zunächst jeweils eine Kopie der Datenbank erstellt und auf dieses arbeitet, weil sie insbesondere die Einträge in der korrekten im Laufe der Bearbeitung noch ändern
- In der Tabelle Fertigungs-Log-Files: Ende Rüsten = Start Bearbeitung 
- Die Zeiten für Ankunft und Abholung eines Transports werden jetzt in beiden Log Files Tabellen getrackt. Das ist eigentlich redundant, aber ich glaube es erleichtert die Auswertung, weil ihr beide auf getrennten Tabellen arbeiten könnt und somit keine joins braucht 
- Ich habe das Rohteillager und das Fertigteillager noch als Betriebsmittelgruppe hinzugefügt, damit aus dem Log-File auch der Anfang und das Ende der Durchlaufzeit erkenntlich ist (Einträge der Art: ('20000000', 'RTL', 0, None, None, None, None) bedeuten Auftragsfreigabe und Einträge der Art: ('20000001', 'FTL', 257.7142857142857, None, None, None, None) bedeuten Ankunft im FTL)
- Alle Zeiten sind aktuell noch als integer gespeichert, weil wir in der Simulation noch nicht mit Zeiten arbeiten sondern einfach hochzählen, das müssen wir als nächstes ändern
- Einträge in den TLF ohne Charge entsprechen Leerfahrten 
- Aktuell ist die Logik bei der FFZ Steuerung so, dass die Fahrzeuge immer an dem Zielort des letzten Auftrags warten
- Wenn ihr Akkustand auf unter 20 % gesunken ist, fahren sie zur Ladestation und werden aufgeladen