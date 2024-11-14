from datetime import datetime
import re
import sqlite3

#todooo: für auswertung nur die betrachten, die freigegeben werden!
#PLAUSIBILITÄT: AUSWERTEN, wann z.B. letzter Drehenzyklus startet
#Abgleich mit Simulationszeit machne!!!


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

#Wichtige globale Variablen, um unnötige Datenbank-abfragen zu vermeiden:

###############
#TLF = getTLF(cursor)
#So ist es besser verständlich!!!
####################

globale_arbeitsplaene = None
globale_auftraege = None
globale_TLF = None

def getTLF(cursor):
    # Hinterlegung des Graphen:
    # RTL - a
    # SAE - b
    # DRH - c
    # FRA - d
    # QPR - e
    # FTL - f
    # Ladestation - g
    knoten_mapping = {
        'a': 'RTL',
        'b': 'SAE',
        'c': 'DRH',
        'd': 'FRA',
        'e': 'QPR',
        'f': 'FTL',
        'g': 'Ladestation'
    }
    global globale_TLF #definition der GLOBALEN varoaelbe

    if globale_TLF is not None:
        return globale_TLF

    cursor.execute("SELECT * FROM TLF")
    raw = cursor.fetchall()
    keys = ['VorgangsNr', 'FFZ_ID', 'Startknoten', 'Endknoten', 'Route', 'Startzeitpunkt', 'Endzeitpunkt', 'Akkustand',
            'Charge']
    TLF = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        Dict['Startzeitpunkt'] = parse_datetime(Dict['Startzeitpunkt'])
        Dict['Endzeitpunkt'] = parse_datetime(Dict['Endzeitpunkt'])
        Dict['Route'] = parse_route(Dict['Route'])

        # Achtung: NONE Werte!
        Dict['Charge'] = int(Dict['Charge']) if Dict['Charge'] is not None else 0

        #Knoten werden hier auf die vorher definierte Position gemapppt!!
        Dict['Startknoten'] = knoten_mapping.get(Dict['Startknoten'], 'Unbekannt')
        Dict['Endknoten'] = knoten_mapping.get(Dict['Endknoten'], 'Unbekannt')

        TLF.append(Dict)

        #globale Variable abspeichern:
        globale_TLF = TLF
    return TLF


#######

#Arbeitspläne in Dictionary umwandeln:
def getAP(cursor):
    global globale_arbeitsplaene

    if globale_arbeitsplaene is not None:
        return globale_arbeitsplaene

    cursor.execute("SELECT * FROM arbeitsplaene")
    raw = cursor.fetchall()
    keys = ['id', 'nr', 'bmg', 'r_plan', 't_plan']
    arbeitsplaene = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        arbeitsplaene.append(Dict)

    globale_arbeitsplaene = arbeitsplaene
    return arbeitsplaene

#Auftragstabelle in Dictionary umwandeln:
def getAuftraege(cursor):
    global globale_auftraege

    if globale_auftraege is not None:
        return globale_auftraege

    cursor.execute("SELECT * FROM auftraege")
    raw = cursor.fetchall()
    keys = ['charge','id', 'stueckzahl_plan', 'stueckzahl_ist', 'freigabe', 'fertigstellung']
    auftraege = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        auftraege.append(Dict)

    globale_auftraege = auftraege
    return auftraege

####1. Testfunktion:
# Prüfen, ob Auftrag genau alle vorgegebenen Stationen aus AP durchläuft
# Das bezieht sich auf eine Charge

#PROBLEM: Was ist mit NONE Einträgen bei der Freigabe?!

#Chargennummer - ist einfach die Nummer der Charge
def AuftragsID(cursor, Chargennummer):
    auftrags_daten = getAuftraege(cursor)
    for eintrag in auftrags_daten:
        if int(eintrag['charge']) == Chargennummer and eintrag['freigabe'] is not None:
            print('Auftrag:', eintrag['id'])
            return eintrag['id'] #Hier wird die Auftragsnummer zurückgegeben
    return None


#Aus AP die einzelnen Stationen ablesen
#Wichtig: gleiche Struktur mit Start-und Endknoten!

#Hier erstmal alle Schritte aus dem Arbeitsplan ableiten
#Achtung: 1. Startknoten muss RTL sein
#Finaler Knoten muss FTL sein

def ArbeitsplanSchritte(cursor, auftrag_id):
    arbeitsplandaten = getAP(cursor)
    Arbeitsplan_Spalten = []
    Arbeitsplan_Spalten.append('RTL')#RTL am Anfang

    for eintrag in arbeitsplandaten:
        if eintrag['id'] == auftrag_id:
            Arbeitsplan_Spalten.append(eintrag['bmg'])
    Arbeitsplan_Spalten.append('FTL')#FTL am ENDEE

    #Vektor wird hier umgewandelt, damit ich den später vergleichen kan
    ArbeitsplanTupel = [(Arbeitsplan_Spalten[i], Arbeitsplan_Spalten[i + 1]) for i in range(len(Arbeitsplan_Spalten) - 1)]
    #print('Arbeitsplaneinträge:', ArbeitsplanTupel)

    return ArbeitsplanTupel if ArbeitsplanTupel else None


def TLF_Schritte(cursor,Chargennummer):
    tlf_daten = getTLF(cursor)
    TLF_Spalten = []
    for eintrag in tlf_daten:
        if int(eintrag['Charge']) == Chargennummer and eintrag['Startknoten'] is not None and eintrag['Endknoten'] is not None:
            TLF_Spalten.append((eintrag['Startknoten'],eintrag['Endknoten']))
    #print('TLFFFFF', TLF_Spalten)
    return TLF_Spalten if TLF_Spalten else None


###DER ULTIMATIVE VERGLEICH

def Vergleich():
    for eintrag in globale_auftraege:
        Chargennummer = eintrag['charge']
        auftrag_id = eintrag['id']  # direkt aus globale_auftraege, falls dort enthalten

        if TLF_Schritte(cursor, Chargennummer) == ArbeitsplanSchritte(cursor, auftrag_id):
            print('juhuu, die stimmen überein')
        else:
            print('hier ist etwas schiefgelaufn')
            print(Chargennummer)
            print(TLF_Schritte(cursor,Chargennummer))
            print(ArbeitsplanSchritte(cursor,auftrag_id))

if globale_auftraege is not None and globale_TLF is not None and globale_arbeitsplaene is not None:
    Vergleich()
    print('ich war hier!!')
else:
    for i in range(2):
        print('programm nochamllll')
        globale_auftraege = getAuftraege(cursor)
        globale_TLF = getTLF(cursor)
        globale_arbeitsplaene = getAP(cursor)
        Vergleich()
        print('ich gehe lieber durch else')

#zu tun: Auswertung:
#woran liegt es, dass es manchmal schief läuft?
#an welchen Stellen läuft es schief?
#lädt da das Gerät?
#vielleicht einfach vektor anzeigen lassen


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

####5. Testfunktion
# ELF: Wird an einer Maschine was produziert, obwohl Maschine zwischen Start- und Endfehler liegt

####6. Aussschuss:
# Wird Ausschussteil trotzdem bei Bestand hinzugefügt?
# auftraege: stueckzahl_ist = stueckzahl_plan - FLF.ausschuss!!!!
#Schließen
conn.close()