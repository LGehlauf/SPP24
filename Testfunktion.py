from datetime import datetime, timedelta
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
globale_FLF = None
globale_ELF = None

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
        'g': 'Ladestation',
        'h':'HAE'
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

#GET FLF!!!

def getFLF(cursor):
    global globale_FLF

    if globale_FLF is not None:
        return globale_FLF

    cursor.execute("SELECT * FROM FLF")
    raw = cursor.fetchall()
    keys = ['Charge','bmg','ankunft', 'start_ruesten', 'start_bearbeitung', 'ende_bearbeitung', 'abtransport', 'anzahl_bauteile', 'ausschuss']
    FLF = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))

        relevante_daten = {
            'Charge': int(Dict['Charge']) if Dict['Charge'] is not None else 0,
            'anzahl_bauteile': int(Dict['anzahl_bauteile']) if Dict['anzahl_bauteile'] is not None else 0,
            'ausschuss': int(Dict['ausschuss']) if Dict['ausschuss'] is not None else 0,
            'bmg': Dict['bmg'] if Dict['bmg'] is not None else "Unbekannt",
            'ankunft': parse_datetime(Dict['ankunft']) if Dict['ankunft'] is not None else None,
            'abtransport': parse_datetime(Dict['abtransport']) if Dict['abtransport'] is not None else None,
            'start_ruesten': parse_datetime(Dict['start_ruesten']) if Dict['start_ruesten'] is not None else None,
            'start_bearbeitung': parse_datetime(Dict['start_bearbeitung']) if Dict['start_bearbeitung'] is not None else None,
            'ende_bearbeitung': parse_datetime(Dict['ende_bearbeitung']) if Dict['ende_bearbeitung'] is not None else None
        }

        FLF.append(relevante_daten)

    # Globale Variable speichern
    globale_FLF = FLF
    return FLF

#GET ELF!
def getELF(cursor):
    global globale_ELF

    if globale_ELF is not None:
        return globale_ELF

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
    globale_ELF = ELF
    return ELF


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


def AuftragsID(cursor, Chargennummer):
    auftrags_daten = getAuftraege(cursor)
    for eintrag in auftrags_daten:
        if int(eintrag['charge']) == Chargennummer and eintrag['freigabe'] is not None:
            print('Auftrag:', eintrag['id'])
            return eintrag['id'] # Hier wird die Auftragsnummer zurückgegeben
    return None


# Aus AP die einzelnen Stationen ablesen
#Wichtig: gleiche Struktur mit Start-und Endknoten!

#Hier erstmal alle Schritte aus dem Arbeitsplan ableiten
#Achtung: 1. Startknoten muss RTL sein
#Finaler Knoten muss FTL sein
#nur fur testfunktion1

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

#TLF-Schritte nimmt daten aus TLF und erstellt für jede charge ein Tupel aus Start und Endknoten
#nur für testfunktion1
def TLF_Schritte(cursor,Chargennummer):
    tlf_daten = getTLF(cursor)
    TLF_Spalten = []
    for eintrag in tlf_daten:
        if int(eintrag['Charge']) == Chargennummer and eintrag['Startknoten'] is not None and eintrag['Endknoten'] is not None:
            TLF_Spalten.append((eintrag['Startknoten'],eintrag['Endknoten']))
    #print('TLFFFFF', TLF_Spalten)
    return TLF_Spalten if TLF_Spalten else ['Simulation erst beenden']


####1. Testfunktion:
# Prüfen, ob Auftrag genau alle vorgegebenen Stationen aus AP durchläuft
# Das bezieht sich auf eine Charge

###DER ULTIMATIVE VERGLEICH

def Testfunktion1():
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
    #Testfunktion1()
    print('tesfunktion1 inaktiv')
else:
    for i in range(2):
        globale_auftraege = getAuftraege(cursor)
        globale_TLF = getTLF(cursor)
        globale_arbeitsplaene = getAP(cursor)
        if globale_TLF is not None:
            #Testfunktion1()
            print('tesfunk1 inaktiv')



####2. Testfunktion:
# Kontinuität
# Wird die Charge auch immer zum abgegebenem Zeitpunkt von einem ffz wieder aufgenommen?

#To do: unbedingt nochmal die zweite testfunktion anschauen
#am logging der daten arbeiten! wie speicher ich das?

def Testfunktion2():
    globale_FLF = getFLF(cursor)
    globale_auftraege = getAuftraege(cursor)
    globale_TLF = getTLF(cursor)

    for auftrag in globale_auftraege:
        Chargennummer = auftrag['charge']

        # Filtere Einträge für die aktuelle Charge
        charge_flf_entries = [entry for entry in globale_FLF if entry['Charge'] == Chargennummer]
        charge_tlf_entries = [entry for entry in globale_TLF if entry['Charge'] == Chargennummer]

        if not charge_flf_entries:
            print(f"Keine FLF-Einträge für Charge {Chargennummer}.")
            continue
        if not charge_tlf_entries:
            print(f"Keine TLF-Einträge für Charge {Chargennummer}.")
            continue

        for flf in charge_flf_entries:
            bmg = flf['bmg']
            ankunftFLF = flf['ankunft']
            abtransportFLF = flf['abtransport']

            # Finde das passende TLF-Eintrag basierend auf Start- oder Endknoten
            passende_tlf_start = next((tlf for tlf in charge_tlf_entries if tlf['Startknoten'] == bmg), None)
            passende_tlf_end = next((tlf for tlf in charge_tlf_entries if tlf['Endknoten'] == bmg), None)

            # RTL Prüfung
            if bmg == 'RTL' and passende_tlf_end:
                endzeitTLF = passende_tlf_end['Endzeitpunkt']
                if ankunftFLF and endzeitTLF:
                    ergebnis1 = endzeitTLF - ankunftFLF
                    if ergebnis1 != timedelta(0):
                        print(Chargennummer)
                        print(f"BMG {bmg}, Ergebnis 1: Ankunft - Startzeitpunkt = {ergebnis1}")
                        print('Endzeit TLF:', endzeitTLF, ' - ', 'Ankunft FLF: ', ankunftFLF)

            # Innere Knoten 1 prüfen
            if bmg not in ['FTL', 'RTL'] and passende_tlf_end:
                endzeitTLF = passende_tlf_end['Endzeitpunkt']
                if ankunftFLF and endzeitTLF:
                    ergebnis2 = ankunftFLF - endzeitTLF
                    if ergebnis2 != timedelta(0):
                        print(Chargennummer)
                        print(f"BMG {bmg}, Ergebnis 2: Ankunft - Endzeitpunkt = {ergebnis2}")
                        print('Ankunft FLF:', ankunftFLF, ' - ', 'Endzeit TLF: ', endzeitTLF)

            # Innere Knoten 2 prüfen
            if bmg not in ['FTL', 'RTL'] and passende_tlf_start:
                startzeitTLF = passende_tlf_start['Startzeitpunkt']
                if abtransportFLF and startzeitTLF:
                    ergebnis3 = abtransportFLF - startzeitTLF
                    if ergebnis3 != timedelta(0):
                        print(Chargennummer)
                        print(f"BMG {bmg}, Ergebnis 3: Abtransport - Startzeitpunkt = {ergebnis3}")
                        print('Abtransport FLF:', abtransportFLF, ' - ', 'Startzeit TLF: ', startzeitTLF)

            # FTL Abtransport prüfen
            if bmg == 'FTL' and passende_tlf_end:
                endzeitTLF = passende_tlf_end['Endzeitpunkt']
                if ankunftFLF and endzeitTLF:
                    ergebnis4 = ankunftFLF - endzeitTLF
                    if ergebnis4 != timedelta(0):
                        print(Chargennummer)
                        print(f"BMG {bmg}, Ergebnis 4: Ankunft - Endzeitpunkt = {ergebnis4}")
                        print('Ankunft FLF:', ankunftFLF, ' - ', 'Endzeit TLF: ', endzeitTLF)

if globale_auftraege is not None and globale_TLF is not None and globale_arbeitsplaene is not None:
    Testfunktion2()
    #print('Testfunktion2 inaktiv')


####3. Testfunktion:
# Bestandserhöhung
# Werden nach erfolgreicher Produktion auch Bestände wirklich erhöt?
# Zusatz: Vermeidung von negativen Beständen (oder Warnung, falls das passiert)
def Testfunktion3():
    globale_FLF = getFLF(cursor)
    globale_auftraege = getAuftraege(cursor)

    for auftrag in globale_auftraege:
        Chargennummer = auftrag['charge']
        stueckzahl_ist = auftrag['stueckzahl_ist']

        charge_flf_entries = [entry for entry in globale_FLF if entry['Charge'] == Chargennummer]

        if not charge_flf_entries:
            print(f"Keine FLF-Einträge für Charge {Chargennummer}.")
            continue

        for i, flf in enumerate(charge_flf_entries):
            bmg = flf['bmg']

            if bmg == 'FTL' and i > 0:
                vorheriger_flf = charge_flf_entries[i - 1]  # Eintrag vor FTL

                vorheriger_anzahl_bauteile = vorheriger_flf['anzahl_bauteile']
                vorheriger_bmg = vorheriger_flf['bmg']

                if stueckzahl_ist == vorheriger_anzahl_bauteile:
                    print(
                        f"Charge {Chargennummer}: Stückzahl Ist ({stueckzahl_ist}) = Bauteile ({vorheriger_anzahl_bauteile}) vor FTL (Station: {vorheriger_bmg}) - Übereinstimmung!"
                    )
                else:
                    print(
                        f"Charge {Chargennummer}: Stückzahl Ist ({stueckzahl_ist}) != Bauteile ({vorheriger_anzahl_bauteile}) vor FTL (Station: {vorheriger_bmg}) - Keine Übereinstimmung!"
                    )
if globale_auftraege is not None and globale_FLF is not None:
    #Testfunktion3()
    print('testfunktion3 inaktiv')
else:
    #diese schleife brauche ich gerade nicht, kann mby weg?!
    for i in range(2):
        globale_auftraege = getAuftraege(cursor)
        globale_FLF = getFLF(cursor)
        if globale_FLF is not None:
            #Testfunktion3()
            print('Testfunktion3 inaktiv')



####4. Testfunktion:
# Schichtende
# Werden Aufträge pausiert, wenn Schicht zu Ende geht?

def Testfunktion4():
    globale_FLF = getFLF(cursor)

    schichtzeiten = {
        'S1': {'start': '06:00', 'end': '14:00'},
        'S2': {'start': '06:00', 'end': '22:00'},
        'S3': {'start': '00:00', 'end': '00:00'},
    }

    schichtregime = 'S2'
    start = datetime.strptime(schichtzeiten[schichtregime]['start'], "%H:%M").time()
    end = datetime.strptime(schichtzeiten[schichtregime]['end'], "%H:%M").time()

    for flf in globale_FLF:
        charge = flf['Charge']
        ankunft = flf['ankunft']
        abtransport = flf['abtransport']
        bmg = flf['bmg']
        start_ruesten = flf['start_ruesten']

        if ankunft is None:
            print(f"Charge {charge}, BMG {bmg}: Keine Ankunftszeit, übersprungen.")
            continue

        #prüfen der ankunftszeit
        if ankunft.time() >= end:
            print(f"Charge {charge}, BMG {bmg}: Ankunft um {ankunft.time()} - Schichtende überschritten.")
        elif ankunft.time() < start:
            print(f"Charge {charge}, BMG {bmg}: Ankunft um {ankunft.time()} - Vor Schichtbeginn.")

        #sonderfall für RTL und FTL
        if abtransport is not None and bmg not in ['RTL', 'FTL']:
            if abtransport.time() >= end:
                print(f"Charge {charge}, BMG {bmg}: Abtransport um {abtransport.time()} - Schichtende überschritten.")
            elif abtransport.time() < start:
                print(f"Charge {charge}, BMG {bmg}: Abtransport um {abtransport.time()} - Vor Schichtbeginn.")
        elif bmg in ['RTL', 'FTL']:
            print(f"Charge {charge}, im {bmg} angekommen.")

        #wird die arbeitszeit überschritten?!
        if ankunft.time() >= end or (abtransport and abtransport.time() >= end):
            print(f"Charge {charge}, BMG {bmg}: Arbeit wird pausiert bis zum nächsten Schichtbeginn ({start_ruesten}).")
        elif ankunft.time() < start:
            print(f"Charge {charge}, BMG {bmg}: Arbeit beginnt erst bei Schichtbeginn um {start_ruesten}.")
        else:
            print(f"Charge {charge}, BMG {bmg}: keine Überschreitung.")


#Testfunktion4()

####5. Testfunktion
# ELF: Wird an einer Maschine was produziert, obwohl Maschine zwischen Start- und Endfehler liegt
#hier stimmt manches noch nicht so ganz:
#lieber die relevante charge ausgeben und genau prüfen, ob alles passt
#das geht auf jeden fall noch simpler!!!
def Testfunktion5():
    globale_ELF = getELF(cursor)
    globale_FLF = getFLF(cursor)

    for elf in globale_ELF:
        vorgangs_nr = elf['Vorgangs_nr']
        bmg_elf = elf['bmg']
        start_downtime = elf['start_downtime']
        end_downtime = elf['end_downtime']

        relevante_flf = [
            flf for flf in globale_FLF
            if elf['bmg'] == flf['bmg'] and
                       (
                               start_downtime <= flf['start_ruesten'] <= end_downtime or
                               start_downtime <= flf['start_bearbeitung'] <= end_downtime or
                               start_downtime <= flf['ende_bearbeitung'] <= end_downtime
                       )
        ]

        if relevante_flf:
            for flf in relevante_flf:
                #variablen
                start_ruesten = flf['start_ruesten']
                start_bearbeitung = flf['start_bearbeitung']
                ende_bearbeitung = flf['ende_bearbeitung']
                #prints:
                # ZUM TESTEN DER TESTFUNKTION:
                # Bedingung von < zu <= ändern!!!
                if start_downtime < start_ruesten < end_downtime:
                    print(f"Downtime für ELF Vorgang {vorgangs_nr}, BMG {bmg_elf}:")
                    print('start der downtime: ', start_downtime)
                    print('start ruesten: ', start_ruesten)
                    print('ende der downtime: ', end_downtime)
                    print('Ruestvorgang zwischen der ELF')

                if start_downtime <= start_bearbeitung <= end_downtime:
                    print(f"Downtime für ELF Vorgang {vorgangs_nr}, BMG {bmg_elf}:")
                    print('start der downtime: ', start_downtime)
                    print('start bearbeitung: ', start_bearbeitung)
                    print('ende der downtime: ', end_downtime)
                    print('Bearbeitungszeit zwischen der ELF')

                #ZUM TESTEN DER TESTFUNKTION:
                #Bedingung von < zu <= ändern!!!
                if start_downtime < ende_bearbeitung < end_downtime:
                    print(f"Downtime für ELF Vorgang {vorgangs_nr}, BMG {bmg_elf}:")
                    print('start der downtime: ', start_downtime)
                    print('ende der bearbeitung: ', ende_bearbeitung)
                    print('ende der downtime: ', end_downtime)
                    print('Bearbeitungsende zwischen der ELF')
        else:
            print('Downtime für ELF Vorgang',vorgangs_nr, 'BMG', bmg_elf, 'wurde korrekt ohne relevante FLF-Daten berücksichtigt.')


#Testfunktion5()


####6. Aussschuss:
# Wird Ausschussteil trotzdem bei Bestand hinzugefügt?
#Aufträge.stueckzahl_plan - FLF.ausschuss = FLF.anzahl_bauteile

def Testfunktion6():
    globale_FLF = getFLF(cursor)
    globale_auftraege = getAuftraege(cursor)

    for auftrag in globale_auftraege:
        Chargennummer = auftrag['charge']
        stueckzahl_plan = auftrag['stueckzahl_plan']

        #hier wird durch flf gefiltert, damit nur stationen gleicher charge untereinander stehen
        charge_flf_entries = [entry for entry in globale_FLF if entry['Charge'] == Chargennummer]

        # falls es noch keine eintröge in flf für die charge gibt
        if not charge_flf_entries:
            print(f"Keine FLF-Einträge für Charge {Chargennummer}.")
            continue
        #gesamter ausschuss für eine charge
        gesamtausschuss = sum(entry['ausschuss'] for entry in charge_flf_entries)

        for i, flf in enumerate(charge_flf_entries):
            bmg = flf['bmg']

            #es wird immer der eintrag vor dem FTL betrachtet
            if bmg == 'FTL' and i > 0:
                vorheriger_flf = charge_flf_entries[i - 1]

                vorheriger_anzahl_bauteile = vorheriger_flf['anzahl_bauteile']
                vorheriger_bmg = vorheriger_flf['bmg']

                #hier ist dann der tatsächliche vergleich
                if stueckzahl_plan - gesamtausschuss == vorheriger_anzahl_bauteile:
                    print(
                        f"Charge {Chargennummer}: Stückzahl Plan ({stueckzahl_plan}) - Ausschuss ({gesamtausschuss}) = Bauteile ({vorheriger_anzahl_bauteile}) - Übereinstimmung! (Station: {vorheriger_bmg})"
                    )
                else:
                    print(
                        f"Charge {Chargennummer}: Stückzahl Plan ({stueckzahl_plan}) - Ausschuss ({gesamtausschuss}) != Bauteile ({vorheriger_anzahl_bauteile}) - Keine Übereinstimmung! (Station: {vorheriger_bmg})"
                    )


#hier die ausführung der testfunktion:
#ich würde in zukunft gerne die ausgabe nicht in der konsole machen sonder irgendwie anders darstellen
if globale_auftraege is not None and globale_TLF is not None and globale_arbeitsplaene is not None:
    #Testfunktion6()
    print('testfunktio6 inaktiv')
else:
    for i in range(2):
        globale_auftraege = getAuftraege(cursor)
        globale_TLF = getTLF(cursor)
        globale_arbeitsplaene = getAP(cursor)
        if globale_TLF is not None:
            print('Testfunktion6 noch inaktiv')
            #Testfunktion6()

#Schließen
conn.close()