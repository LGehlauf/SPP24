
import sqlite3
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import math


#Menge an geplotten Daten
laenge = 170

#Verschiebeung von Abgangskurve nach hinten um Stunden
h = 0

# Verbindung zur Datenbank herstellen
verbindung = sqlite3.connect("prod_data.db")
zeiger = verbindung.cursor()

# Abrufen der Maschinen aus der Datenbank
zeiger.execute("SELECT DISTINCT bmg FROM FLF")
maschinen = zeiger.fetchall()

# Funktion zur Berechnung der Betriebsstunden in Stunden seit dem ersten Produktionstag
def berechne_betriebs_stunden(zeitpunkt, start_datum):
    """Berechnet die Betriebsstunden seit dem ersten Produktionstag"""
    return (zeitpunkt - start_datum).total_seconds() / 3600  # Umrechnung von Sekunden in Stunden

# Erstellen eines Diagramms für jede Maschine
for maschine in maschinen:
    maschine_name = maschine[0]
    
    # Daten für die aktuelle Maschine holen
    zeiger.execute(f"SELECT ankunft, ende_bearbeitung, anzahl_bauteile, anzahl_bauteile + ausschuss AS plan FROM FLF WHERE bmg = '{maschine_name}'")
    daten = zeiger.fetchall()
    
    # Umwandeln der Daten in datetime-Objekte und sicherstellen, dass keine None-Werte enthalten sind
    ankunft_liste = []
    fertigstellung_liste = []
    vorgabe_liste = []
    real_liste = []
    
    for e in daten:
        # Wenn die Werte nicht None sind, führe das Parsing durch
        if e[0] is not None and e[1] is not None:
            ankunft_liste.append(datetime.strptime(e[0], '%Y-%m-%d %H:%M:%S'))
            fertigstellung_liste.append(datetime.strptime(e[1], '%Y-%m-%d %H:%M:%S'))
            vorgabe_liste.append(int(e[3])) 
            real_liste.append(int(e[2])) # Vorgabe ist der Arbeitsinhalt

    #verschieben der Abgangskurve um 4 Stunden nach hinten zur besseren Visualiesierung 
    fertigstellung_liste = [e + timedelta(hours=h) for e in fertigstellung_liste]
    
    # Prüfen, ob die Listen leer sind, bevor wir mit min() fortfahren
    if not ankunft_liste:
        print(f"Keine gültigen Startzeiten für Maschine {maschine_name} gefunden.")
        continue
    
    # Berechnen des ersten Produktionsdatums
    start_datum = min(ankunft_liste)
    
    # Berechnen der Betriebsstunden für Zugang und Abgang
    zugang_stunden = [berechne_betriebs_stunden(e, start_datum) for e in ankunft_liste]
    abgang_stunden = [berechne_betriebs_stunden(e, start_datum) for e in fertigstellung_liste]
    
    # Kumulative Summe für die Zugangskurve und Abgangskurve
    kumulierte_zugang = [sum(vorgabe_liste[:i+1]) for i in range(len(vorgabe_liste))]
    kumulierte_abgang = [sum(real_liste[:i+1]) for i in range(len(real_liste))]


    import numpy as np

    # Gemeinsame x-Werte für Zugang und Abgang finden
    gemeinsame_x = np.union1d(zugang_stunden, abgang_stunden)

    # Interpolierte y-Werte für kumulierte Zugang und Abgang
    kumulierte_zugang_interp = np.interp(gemeinsame_x, zugang_stunden, kumulierte_zugang)
    kumulierte_abgang_interp = np.interp(gemeinsame_x, abgang_stunden, kumulierte_abgang)



    print(ankunft_liste)
    #print(fertigstellung_liste)
    print (start_datum)
    print(kumulierte_zugang)
    print(zugang_stunden)
    #print(kumulierte_abgang)
    #print(kumulierte_abgang_interp)
    #print(kumulierte_zugang_interp)



    # Berechnung der mittleren Größen
    P = max(abgang_stunden) - min(zugang_stunden)  # Bezugzeitraum in Stunden
    Bm = sum(vorgabe_liste) / len(vorgabe_liste)  # Durchschnittlicher Bestand
    Rm = Bm / (P / len(zugang_stunden))  # Mittlere Reichweite
    Lm = kumulierte_abgang[-1] / P  # Mittlere Leistung



  

    #y = Lm * zugang_stunden

    # Visualisierung des Diagramms für die Maschine
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Zugangskurve (blau)
    ax.step(zugang_stunden[:laenge], kumulierte_zugang[:laenge], label='Zugangskurve', color='blue', where='mid')
    
    
    # Abgangskurve (rot)
    ax.step(abgang_stunden[:laenge], kumulierte_abgang[:laenge], label='Abgangskurve', color='red', where='mid')
    #ax.plot(abgang_stunden[:laenge], abgang_stunden_multipliziert[:laenge],color = 'gray')

    # Mittlerer Bestand als schattierte Fläche zwischen Zugang und Abgang
    ax.fill_between(zugang_stunden[:laenge], kumulierte_zugang[:laenge], color='grey', step='mid', alpha=0.7, label='Bestandsfläche FB')
    ax.fill_between(abgang_stunden[:laenge], kumulierte_abgang[:laenge], color='white', step='mid',interpolate= False, alpha=1)
    
    
    # Linien für die mittleren Werte
    ax.axhline(Bm, color='green', linestyle='--', label=f'Mittlerer Bestand Bm = {Bm:.2f}')
    ax.axhline(Lm, color='purple', linestyle='--', label=f'Mittlere Leistung Lm = {Lm:.2f}')
    ax.axvline(Rm, color='orange', linestyle='--', label=f'Mittlere Reichweite Rm = {Rm:.2f}')
    
    # Diagrammdetails
    ax.set_xlabel("Betriebsstunden")
    ax.set_ylabel("Kumulierte Arbeitsinhalte in Stk.")
    ax.set_title(f"Durchlaufdiagramm für Maschine {maschine_name}")
    ax.legend(loc='upper left')
    ax.grid(True)

    # Layout anpassen und Diagramm anzeigen
    plt.tight_layout()
    plt.show()

# Verbindung zur Datenbank schließen
verbindung.close()

#Für gesamte Fertigung Freigabeauftrag und Fertigstellung 
#Wenn pro Maschine dann auch Lagermenge davor betrachten 
#ohne Downtimes (Schichtende, Wochenende)



#Funktion mit Angabe Start- und Enddatum 
#Diagramme für Maschinen --> Welcher Aufträge waren auf welchen Maschinen 
#Wie Plantafel für Fertigung 