#+3 Datenbanken
#1. Vergleicht, wie viel Reststandzeit verschenkt wird (Summe REststandzeit)?
#2. Wie viel prozent planed/unplaned?
#3. Wie lange waren Stillstände? (Enddonwtime-Startdowntime)?
from datetime import datetime, timedelta
import re
import sqlite3
globale_ELF1 = None

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
def getELF1(cursor):
    conn = sqlite3.connect('prod_data.db')
    cursor = conn.cursor()
    global globale_ELF1

    if globale_ELF1 is not None:
        return globale_ELF1

    cursor.execute("SELECT * FROM ELF")
    raw = cursor.fetchall()
    keys = ['Vorgangs_nr','bmg','start_downtime','end_downtime']
    ELF = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))

        relevante_daten = {
            'Vorgangs_nr': int(Dict['Vorgangs_nr']) if Dict['Vorgangs_nr'] is not None else 0,
            'bmg': Dict['bmg'] if Dict['bmg'] is not None else "Unbekannt",
            'start_downtime': parse_datetime(Dict['start_downtime']) if Dict['start_downtime'] is not None else None,
            'end_downtime': parse_datetime(Dict['end_downtime']) if Dict['end_downtime'] is not None else None
        }

        ELF.append(relevante_daten)

    # Globale Variable speichern
    globale_ELF1 = ELF
    return ELF
    conn.close()



