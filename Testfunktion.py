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
        TLF.append(Dict)
    return TLF
#######
#print(getTLF(cursor))

####1. Testfunktion:
# Prüfen, ob Auftrag genau alle vorgegebenen Stationen aus AP durchläuft
# Das bezieht sich auf eine Charge
# 

#Schließen
conn.close()