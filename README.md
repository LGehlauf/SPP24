# SPP24
# 02.11.2024 Karl Marbach
Notes für Jasper und Leo
- FLF = Fertigungs-Log-Files, TLF = Transport-Log-Files
- Ich empfehle, dass ihr euch für eure Zwecke zunächst jeweils eine Kopie der Datenbank erstellt und auf dieses arbeitet, weil sie insbesondere die Einträge in der korrekten im Laufe der Bearbeitung noch ändern
- In der Tabelle Fertigungs-Log-Files: Ende Rüsten = Start Bearbeitung 
- Die Zeiten für Ankunft und Abholung eines Transports werden jetzt in beiden Log Files Tabellen getrackt. Das ist eigentlich redundant, aber ich glaube es erleichtert die Auswertung, weil ihr beide auf getrennten Tabellen arbeiten könnt und somit keine joins braucht 
- Ich habe das Rohteillager und das Fertigteillager noch als Betriebsmittelgruppe hinzugefügt, damit aus dem Log-File auch der Anfang und das Ende der Durchlaufzeit erkenntlich ist (Einträge der Art: ('20000000', 'RTL', 0, None, None, None, None) bedeuten Auftragsfreigabe und Einträge der Art: ('20000001', 'FTL', 257.7142857142857, None, None, None, None) bedeuten Ankunft im FTL)
- Ich habe einen Kalender implementiert, die Zeiten in der DB sind als integer gespeichert, weil SQLite laut ChatGBT kein datetime unterstützt
- Einträge in den TLF ohne Charge entsprechen Leerfahrten 
- Aktuell ist die Logik bei der FFZ Steuerung so, dass die Fahrzeuge immer an dem Zielort des letzten Auftrags warten
- Wenn ihr Akkustand auf unter 20 % gesunken ist, fahren sie zur Ladestation und werden aufgeladen

# 03.11.2024 Karl Marbach
- Ich habe noch eine Engpasssteuerung als Auftragsfreigabeverfahren integriert, d.h. die Aufträge werden nun nach dem Bestellbestandsverfahren erzeugt, aber jeweils erst freigegeben, wenn der Bestand am Engpasssystem ein definiertes Level (z.b. 5 Arbeitsstunden) unterschreitet, damit können wir das Verstopfen der Produktion und stark schwankende Durchlaufzeiten vermeiden, wenn wir jetzt nach und nach neue Produkte ergänzen 
- für Jasper: die DLZ ist jetzt aus der Auftragstabelle ablesbar, das erleichtert die Auswertung nochmal
- ich habe jetzt auch noch die Fräsmaschine mit einem Produkt in Betrieb genommen
- Es gibt jetzt auch einen Betriebskalender, welcher die Arbeiten je nach gewähltem Schichtregime zwischen 14:00 - 06:00 bzw. 22:00 - 06:00 pausiert, und Arbeit am Wochenende vermeidet

# 09.11.2024 Karl Marbach
- Ausschuss wird absofort mitsumuliert, er ergibt sich durch ziehen von Zufallszahlen aus einer Binomialverteilung mit Parametern n = Losgröße und p = Ausschussrate der Maschine, die jeweiligen Ausschüsse sind pro Maschine in den FLF bzw. pro Auftrag in der auftraege Tabelle abzulesen
- Die Rüst- und Bearbeitungszeiten werden jetzt ebenfalls als Zufallszahlen aus einer linkssteilen Log-Normalverteilung gezogen (Mittelwert = Planbearbeitungzeit, Stabw = 6,67 % der Planbearbeitungszeit)
- Maschinenausfälle werden jetzt simuliert, die Wartezeit zwischen zwei Ausfällen ist exponentialverteilt, die Ausfälle sind in einer neuen Tabelle Error-Log-Files (ELF) auszulesen
- Für Jasper: Wenn du die OEE für einzelne Anlagen berechnen möchtest, kannst du die ungeplante Stillstandszeit aufgrund von Ausfällen aus ELF bekommen und die geplante Stillstandszeit aufgrund mangelnder Belegung aus FLF (als Summe der Zeiten, in welchen keine Bearbeitung stattfindet)
- Für David: weitere Testcases:
    - Wird an einer Maschine produziert, während sie aufgrund eines Ausfalls gewartet wird?
    - Erhöht sich der Bestand im FTL jeweils nur um die tatsächlich produzierten Bauteile (also wird der Ausschuss beachtet?)


