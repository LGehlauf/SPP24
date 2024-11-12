from datetime import datetime
import re
import sqlite3


#Hier erstmal die connection aufbauen
#cursor!
conn = sqlite3.connect('prod_data.db')
cursor = conn.cursor()

#Leo's coole getTLF-Magie :)
########
def parse_datetime(datums_string):
    for format in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(datums_string, format)
        except ValueError:
            continue
    raise ValueError(f"Datumsformat von '{datums_string}' ist unbekannt")

def parse_route(route_string:str) -> list[tuple]:
    matches = re.findall(r"([a-z])", route_string)
    return tuple(matches)

def getTLF(cursor):
    cursor.execute("SELECT * FROM TLF")
    raw = cursor.fetchall()
    keys = ['VorgangsNr', 'FFZ_ID', 'Startknoten', 'Endknoten', 'Route', 'Startzeitpunkt', 'Endzeitpunkt', 'Akkustand', 'Charge']
    TLF = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        Dict['Startzeitpunkt'] = parse_datetime(Dict['Startzeitpunkt'])
        Dict['Endzeitpunkt'] = parse_datetime(Dict['Endzeitpunkt'])
        Dict['Route'] = parse_route(Dict['Route'])
        #Achtung: NONE werte!!
        Dict['Charge'] = int(Dict['Charge']) if Dict['Charge'] is not None else 0

        TLF.append(Dict)
    return TLF

#######

#Arbeitspläne in Dictionary umwandeln:
def getAP(cursor):
    cursor.execute("SELECT * FROM arbeitsplaene")
    raw = cursor.fetchall()
    keys = ['id', 'nr', 'bmg', 'r_plan', 't_plan']
    arbeitsplaene = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        arbeitsplaene.append(Dict)
    return arbeitsplaene

#Auftragstabelle in Dictionary umwandeln:
def getAuftraege(cursor):
    cursor.execute("SELECT * FROM auftraege")
    raw = cursor.fetchall()
    keys = ['charge','id', 'stueckzahl_plan', 'stueckzahl_ist', 'freigabe', 'fertigstellung']
    auftraege = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        auftraege.append(Dict)
    return auftraege


####1. Testfunktion:
# Prüfen, ob Auftrag genau alle vorgegebenen Stationen aus AP durchläuft
# Das bezieht sich auf eine Charge

#Aus TLF die Stationen einer Charge auslesen:
tlf_daten = getTLF(cursor)
for keys in tlf_daten:
    if int(keys['Charge']) == 20000001:
        print("Startknoten:", keys['Startknoten'])
        print("Endknoten:", keys['Endknoten'])
        break

#Das klappt!
# ToDo für jede Charge den Auftrag zuordnen und mit dem AP vergleichen!

#ID der Charge aus der Auftragstabelle kriegen:

#auftraege = getAuftraege(cursor)
#for auftrag in auftraege:
#    print("Charge ID:", auftrag['charge'])

####2. Testfunktion:
# Kontinuität
# Wird die Charge auch immer zum abgegebenem Zeitpunkt von einem ffz wieder aufgenommen?

####3. Testfunktion:
# Bestandserhöhung
# Werden nach erfolgreicher Produktion auch Bestände wirklich erhöt?
# Zusatz: Vermeidung von negativen Beständen (oder Warnung, falls das passiert)

####4. Testfunktion:
# Schichtende
# Werden Aufträge pausiert, wenn Schicht zu Ende geht?

#Schließen
conn.close()