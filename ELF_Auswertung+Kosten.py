from datetime import datetime, timedelta
import re
import sqlite3
import matplotlib.pyplot as plt

globale_ELF_nomaintenance = None
globale_ELF_planned = None
globale_ELF_predictive = None

# Kosten pro Stunde
device_costs = {
    "SAE": 1.15,
    "DRH1": 14.84,
    "DRH2": 14.84,
    "FRA": 17.77,
    "HAE": 10
}

# Standzeiten und Kosten pro Maschine
standzeiten = {
    "SAE" : 850,
    "FRA": 880,   # Stunden
    "DRH1": 1100,  # Stunden
    "DRH2": 900,  # Stunden
    "HAE": 1500   # Stunden
}

kostensaetze = {
    "SAE" : 100,
    "FRA": 200,  # Euro
    "DRH1": 500, # Euro
    "DRH2": 500, # Euro
    "HAE": 100   # Euro
}

# Kosten pro Stunde
kosten_pro_stunde = {
    maschine: kostensaetze[maschine] / standzeiten[maschine]
    for maschine in standzeiten
}

def parse_datetime(datums_string):
    for format in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(datums_string, format)
        except ValueError:
            continue
    raise ValueError(f"Datumsformat von '{datums_string}' ist unbekannt")

def parse_route(route_string: str) -> list[tuple]:
    matches = re.findall(r"([a-z])", route_string)
    return tuple(matches)

def getELF1():
    conn = sqlite3.connect('prod_data_no_maintenance.db')
    cursor = conn.cursor()
    global globale_ELF_nomaintenance

    if globale_ELF_nomaintenance is not None:
        return globale_ELF_nomaintenance
    try:
        cursor.execute("SELECT * FROM ELF")
        raw = cursor.fetchall()
        keys = ['Vorgangs_nr','bmg','start_downtime','end_downtime','reststandzeit','type']
        ELF = []
        for tupel in raw:
            Dict = dict(zip(keys, tupel))

            relevante_daten = {
                'Vorgangs_nr': int(Dict['Vorgangs_nr']) if Dict['Vorgangs_nr'] is not None else 0,
                'bmg': Dict['bmg'] if Dict['bmg'] is not None else "Unbekannt",
                'start_downtime': parse_datetime(Dict['start_downtime']) if Dict['start_downtime'] is not None else None,
                'end_downtime': parse_datetime(Dict['end_downtime']) if Dict['end_downtime'] is not None else None,
                'reststandzeit': int(Dict['reststandzeit']) if Dict['reststandzeit'] is not None else 0,
                'type': Dict['type'] if Dict['type'] is not None else "Unbekannt"
            }

            ELF.append(relevante_daten)

        globale_ELF_nomaintenance = ELF
        return ELF
    finally:
        conn.close()

def getELF2():
    conn = sqlite3.connect('prod_data_planed_maintenance.db')
    cursor = conn.cursor()
    global globale_ELF_planned

    if globale_ELF_planned is not None:
        return globale_ELF_planned
    try:
        cursor.execute("SELECT * FROM ELF")
        raw = cursor.fetchall()
        keys = ['Vorgangs_nr','bmg','start_downtime','end_downtime','reststandzeit','type']
        ELF = []
        for tupel in raw:
            Dict = dict(zip(keys, tupel))

            relevante_daten = {
                'Vorgangs_nr': int(Dict['Vorgangs_nr']) if Dict['Vorgangs_nr'] is not None else 0,
                'bmg': Dict['bmg'] if Dict['bmg'] is not None else "Unbekannt",
                'start_downtime': parse_datetime(Dict['start_downtime']) if Dict['start_downtime'] is not None else None,
                'end_downtime': parse_datetime(Dict['end_downtime']) if Dict['end_downtime'] is not None else None,
                'reststandzeit': int(Dict['reststandzeit']) if Dict['reststandzeit'] is not None else 0,
                'type': Dict['type'] if Dict['type'] is not None else "Unbekannt"
            }

            ELF.append(relevante_daten)

        globale_ELF_planned = ELF
        return ELF
    finally:
        conn.close()

def getELF3():
    global globale_ELF_predictive
    if globale_ELF_predictive is not None:
        return globale_ELF_predictive

    conn = sqlite3.connect('prod_data_predictive_maintenance.db')
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM ELF")
        raw = cursor.fetchall()
        keys = ['Vorgangs_nr', 'bmg', 'start_downtime', 'end_downtime', 'reststandzeit', 'type']
        ELF = []

        for tupel in raw:
            Dict = dict(zip(keys, tupel))
            relevante_daten = {
                'Vorgangs_nr': int(Dict['Vorgangs_nr']) if Dict['Vorgangs_nr'] is not None else 0,
                'bmg': Dict['bmg'] if Dict['bmg'] is not None else "Unbekannt",
                'start_downtime': parse_datetime(Dict['start_downtime']) if Dict['start_downtime'] else None,
                'end_downtime': parse_datetime(Dict['end_downtime']) if Dict['end_downtime'] else None,
                'reststandzeit': int(Dict['reststandzeit']) if Dict['reststandzeit'] is not None else 0,
                'type': Dict['type'] if Dict['type'] else "Unbekannt"
            }
            ELF.append(relevante_daten)

        globale_ELF_predictive = ELF
        return ELF
    finally:
        conn.close()

def berechne_kosten_reststandzeiten(elf_data):
    kosten_pro_maschine_rst = {maschine: 0 for maschine in standzeiten.keys()}
    gesamt_kosten_rst = 0

    for entry in elf_data:
        maschine = entry['bmg']
        reststandzeit = entry['reststandzeit']

        if maschine in kosten_pro_stunde and reststandzeit:
            kosten = reststandzeit / 60 * kosten_pro_stunde[maschine]  # Reststandzeit in Stunden
            kosten_pro_maschine_rst[maschine] += kosten
            gesamt_kosten_rst += kosten

    kosten_pro_maschine_rst = {maschine: round(kosten, 2) for maschine, kosten in kosten_pro_maschine_rst.items()}
    gesamt_kosten_rst = round(gesamt_kosten_rst, 2)



    return gesamt_kosten_rst, kosten_pro_maschine_rst

def vergleiche_kosten_reststandzeiten(ax):
    elf_nomaintenance = getELF1()
    elf_planned = getELF2()
    elf_predictive = getELF3()

    kosten_nomaintenance, kosten_pro_maschine_nomaintenance = berechne_kosten_reststandzeiten(elf_nomaintenance)
    kosten_planned, kosten_pro_maschine_planned = berechne_kosten_reststandzeiten(elf_planned)
    kosten_predictive, kosten_pro_maschine_predictive = berechne_kosten_reststandzeiten(elf_predictive)

    print("\nKosten für die Reststandzeiten der drei ELFs:")
    print("\nNo Maintenance ELF:")
    print(f"Gesamtkosten: {kosten_nomaintenance:.2f} €")
    print(f"Kosten pro Maschine: {kosten_pro_maschine_nomaintenance}")

    print("\nPlanned ELF:")
    print(f"Gesamtkosten: {kosten_planned:.2f} €")
    print(f"Kosten pro Maschine: {kosten_pro_maschine_planned}")

    print("\nPredictive ELF:")
    print(f"Gesamtkosten: {kosten_predictive:.2f} €")
    print(f"Kosten pro Maschine: {kosten_pro_maschine_predictive}")

    print("-----------------")

    ax.set_yscale('log')
    ax.set_ylim(1, 1000000)

    labels = ['No Maintenance', 'Planned', 'Predictive']
    gesamt_kosten_rst = [kosten_nomaintenance, kosten_planned, kosten_predictive]
    create_subplot_plot(ax, gesamt_kosten_rst, labels, plot_type='bar',
                        title='Vergleich der Gesamtkosten durch Reststandzeit', xlabel='', ylabel='Kosten [€]')



#####PLOTS:
def create_subplot_plot(ax, data, labels, plot_type='bar', title='Diagramm', xlabel='X-Achse', ylabel='Y-Achse', stacked_data=None):
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if plot_type == 'bar':
        if stacked_data is None:
            # Fuer Plots 1,3 und 4
            bars = ax.bar(labels, data, color='skyblue')
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, height + 0.01, f'{height:.2f}',
                            ha='center', va='bottom', fontsize=10)
        else:
            # Gestapeltes Balkendiagramm
            # Fuer PLot 2
            bars1 = ax.bar(labels, data, color='skyblue', label='Geplante Downtime')
            ax.bar(labels, stacked_data, bottom=data, color='orange', label='Ungeplante Downtime')
            ax.legend()

            for i, bar in enumerate(bars1):
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2, height + 0.5, f'{height:.2f}%',
                            ha='center', va='bottom', fontsize=10)

    else:
        raise ValueError(f"Unbekannter Plot-Typ: {plot_type}")

def rst(globale_ELF_nomaintenance, globale_ELF_planned, globale_ELF_predictive,ax):
    def berechne_summe(ELF):
        return sum(entry['reststandzeit'] for entry in ELF if entry.get('reststandzeit') is not None)

    summe_nomaintenance = berechne_summe(globale_ELF_nomaintenance)
    summe_planned = berechne_summe(globale_ELF_planned)
    summe_predictive = berechne_summe(globale_ELF_predictive)

    max_summe = max(summe_nomaintenance, summe_planned, summe_predictive)
    print("Summe der Reststandzeit bei No Maintenance: ",summe_nomaintenance, "Min")
    print("Summe der Reststandzeit bei Planned: ",summe_planned, "Min")
    print("Summe der Reststandzeit bei Predictive: ",summe_predictive, "Min")

    if max_summe == summe_nomaintenance:
        print("Die Summe der Reststandzeit ist bei 'No Maintenance' am höchsten.")
    elif max_summe == summe_planned:
        print("Die Summe der Reststandzeit ist bei 'Planned' am höchsten.")
    elif max_summe == summe_predictive:
        print("Die Summe der Reststandzeit ist bei 'Predictive' am höchsten.")

    print("-----------------")

    # 1. Plot:
    labels = ['No Maintenance', 'Planned', 'Predictive']
    data = [summe_nomaintenance, summe_planned, summe_predictive]

    ax.set_yscale('log')
    ax.set_ylim(1, 1000000)

    create_subplot_plot(ax, data, labels, plot_type='bar', title='Summe der Reststandzeiten', xlabel='',
                        ylabel='Reststandzeit [Min]', stacked_data=None)

    return summe_nomaintenance, summe_planned, summe_predictive        

# (Für getELF2 und getELF3 bleibt der Code unverändert)

# 2. Prozent von unplaned und planed
def berechne_type_prozent(elf_data):
    total = len(elf_data)
    if total == 0:
        return {'planed': 0, 'unplaned': 0}

    planed_count = sum(1 for entry in elf_data if entry['type'] == "planed")
    unplaned_count = sum(1 for entry in elf_data if entry['type'] == "unplaned")

    return {
        'planed': (planed_count / total) * 100,
        'unplaned': (unplaned_count / total) * 100
    }


def vergleiche_type_prozent(ax):
    elf_nomaintenance = getELF1()
    elf_planned = getELF2()
    elf_predictive = getELF3()

    nomaintenance_prozent = berechne_type_prozent(elf_nomaintenance)
    planned_prozent = berechne_type_prozent(elf_planned)
    predictive_prozent = berechne_type_prozent(elf_predictive)

    print("\n")
    print("Anteil von 'planned' und 'unplanned' für die drei ELFs:")
    print("\nNo Maintenance ELF:")
    print(f"Planed: {nomaintenance_prozent['planed']:.2f}%")
    print(f"Unplaned: {nomaintenance_prozent['unplaned']:.2f}%")

    print("\nPlanned ELF:")
    print(f"Planed: {planned_prozent['planed']:.2f}%")
    print(f"Unplaned: {planned_prozent['unplaned']:.2f}%")

    print("\nPredictive ELF:")
    print(f"Planed: {predictive_prozent['planed']:.2f}%")
    print(f"Unplaned: {predictive_prozent['unplaned']:.2f}%")

    print("-----------------")

    # 2. Plot
    # gestapeltes Balkendiagramm
    labels = ['No Maintenance', 'Planned', 'Predictive']
    planed_data = [nomaintenance_prozent['planed'], planned_prozent['planed'], predictive_prozent['planed']]
    unplaned_data = [nomaintenance_prozent['unplaned'], planned_prozent['unplaned'], predictive_prozent['unplaned']]

    create_subplot_plot(ax, planed_data, labels, plot_type='bar', title='Vergleich geplanter und ungeplanter Downtime',
                        xlabel='', ylabel='Downtime [%]', stacked_data=unplaned_data)

#3. Vergleiche Downtimeee
def berechne_downtime(elf_data):
    downtime_list = []
    for entry in elf_data:
        start_downtime = entry['start_downtime']
        end_downtime = entry['end_downtime']

        if start_downtime and end_downtime:
            downtime = end_downtime - start_downtime
            downtime_in_minutes = downtime.total_seconds() / 60
            downtime_list.append(downtime_in_minutes)
        else:
            downtime_list.append(0)
    return downtime_list




def vergleiche_downtime(ax1,ax2):
    elf_nomaintenance = getELF1()
    elf_planned = getELF2()
    elf_predictive = getELF3()

    nomaintenance_downtime = berechne_downtime(elf_nomaintenance)
    planned_downtime = berechne_downtime(elf_planned)
    predictive_downtime = berechne_downtime(elf_predictive)
    def durchschnittliche_downtime(downtime_list):
        if downtime_list:
            return sum(downtime_list) / len(downtime_list)
        return 0


    nomaintenance_avg = round(durchschnittliche_downtime(nomaintenance_downtime),2)
    planned_avg = round(durchschnittliche_downtime(planned_downtime),2)
    predictive_avg = round(durchschnittliche_downtime(predictive_downtime),2)
    summe_nomaintenance = sum(nomaintenance_downtime)
    summe_planned = sum(planned_downtime)
    summe_predictive = sum(predictive_downtime)

    verbesserung_planned = round((1 - (summe_planned / summe_nomaintenance))*100,2)
    verbesserung_predictive = round((1- (summe_predictive / summe_nomaintenance))*100,2)

    print("\n")

    # Ergebnisse ausgeben
    print("Durchschnittliche Downtime (in Minuten) für die drei ELFs:")
    print("\nNo Maintenance ELF:")
    print("Durchschnittliche Downtime:",nomaintenance_avg, "Minuten")
    print("Downtime insgesamt:", summe_nomaintenance, "Minuten")

    print("\nPlanned ELF:")
    print("Durchschnittliche Downtime:", planned_avg, "Minuten")
    print("Downtime insgesamt:", summe_planned, "Minuten")
    print("Verbesserung:", verbesserung_planned, "%")

    print("\nPredictive ELF:")
    print("Durchschnittliche Downtime:",predictive_avg, "Minuten")
    print("Downtime insgesamt:", summe_predictive, "Minuten")
    print("Verbesserung:", verbesserung_predictive, "%")

    print("-----------------")


    # 3. Plot
    # Durchschnittliche Downtime
    avg_downtime = [nomaintenance_avg, planned_avg, predictive_avg]
    labels = ['No Maintenance', 'Planned', 'Predictive']
    create_subplot_plot(ax1, avg_downtime, labels, plot_type='bar', title='Durchschnittliche Downtime', xlabel='',
                        ylabel='Durchschnittliche Downtime [Min]', stacked_data=None)
    # 4. Plot
    # Gesamte Downtime
    total_downtime = [summe_nomaintenance, summe_planned, summe_predictive]
    ax2.bar(labels, total_downtime, color='orange')
    create_subplot_plot(ax2, total_downtime, labels, plot_type='bar', title='Gesamte Downtime', xlabel='',
                        ylabel='Gesamte Downtime [Min]', stacked_data=None)
    


def berechne_kosten(elf_data):
    kosten_pro_maschine = {"SAE": 0 , "DRH": 0 ,"FRA": 0 , "HAE" : 0 }
    gesamt_kosten = 0

    for entry in elf_data:
        start_downtime = entry['start_downtime']
        end_downtime = entry['end_downtime']
        maschine = entry['bmg']

        if start_downtime and end_downtime and maschine in device_costs:
            downtime = (end_downtime - start_downtime).total_seconds() / 3600  # Downtime in Stunden
            kosten = downtime * device_costs[maschine]
            gesamt_kosten += kosten

        if maschine == "DRH1" or maschine == "DRH2":
            kosten_pro_maschine["DRH"] += kosten
        else:
            kosten_pro_maschine[maschine] += kosten  

    kosten_pro_maschine = {maschine: round(kosten, 2) for maschine, kosten in kosten_pro_maschine.items()}
    gesamt_kosten = round(gesamt_kosten, 2)           

    return gesamt_kosten, kosten_pro_maschine

def vergleiche_kosten(ax):
    elf_nomaintenance = getELF1()
    elf_planned = getELF2()
    elf_predictive = getELF3()

    kosten_nomaintenance, kosten_pro_maschine_nomaintenance = berechne_kosten(elf_nomaintenance)
    kosten_planned, kosten_pro_maschine_planned = berechne_kosten(elf_planned)
    kosten_predictive, kosten_pro_maschine_predictive = berechne_kosten(elf_predictive)

    print("Kosten durch Stillstand für die drei ELFs:")
    print("\nNo Maintenance ELF:")
    print(f"Gesamtkosten: {kosten_nomaintenance:.2f} €")
    print(f"Kosten pro Maschine: {kosten_pro_maschine_nomaintenance} " )

    print("\nPlanned ELF:")
    print(f"Gesamtkosten: {kosten_planned:.2f} €")
    print(f"Kosten pro Maschine: {kosten_pro_maschine_planned} ")

    print("\nPredictive ELF:")
    print(f"Gesamtkosten: {kosten_predictive:.2f} €")
    print(f"Kosten pro Maschine: {kosten_pro_maschine_predictive} ")

    print("-----------------")

    # 5. Plot - Kostenvergleich
    labels = ['No Maintenance', 'Planned', 'Predictive']
    gesamt_kosten = [kosten_nomaintenance, kosten_planned, kosten_predictive]
    create_subplot_plot(ax, gesamt_kosten, labels, plot_type='bar',
                        title='Vergleich der Gesamtkosten durch Downtime', xlabel='', ylabel='Kosten [€]')


def berechne_gesamtkosten(elf_data):
    """
    Berechnet die Gesamtkosten aus den Stillstandszeit-Kosten und den übrigen Reststandzeit-Kosten.
    """
    # Stillstandszeitkosten berechnen
    gesamt_kosten_downtime, kosten_pro_maschine_downtime = berechne_kosten(elf_data)

    # Kosten durch Reststandzeit berechnen
    gesamt_kosten_rst, kosten_pro_maschine_rst = berechne_kosten_reststandzeiten(elf_data)

    return gesamt_kosten_downtime, gesamt_kosten_rst, gesamt_kosten_downtime + gesamt_kosten_rst

def darstellung_gesamtkosten():
    """
    Erstellt ein Balkendiagramm, das die Gesamtkosten sowie die Anteile für Stillstandszeit und Reststandzeit zeigt.
    """
    elf_nomaintenance = getELF1()
    elf_planned = getELF2()
    elf_predictive = getELF3()

    labels = ['No Maintenance', 'Planned', 'Predictive']
    kosten_downtime = []
    kosten_rst = []
    gesamt_kosten = []

    for elf_data in [elf_nomaintenance, elf_planned, elf_predictive]:
        kosten_dt, kosten_rst_ind, gesamt = berechne_gesamtkosten(elf_data)
        kosten_downtime.append(kosten_dt)
        kosten_rst.append(kosten_rst_ind)
        gesamt_kosten.append(gesamt)

    # Balkendiagramm erstellen
    fig, ax = plt.subplots(figsize=(10, 6))

    # Gestapelte Balken
    bars_downtime = ax.bar(labels, kosten_downtime, color='skyblue', label='Kosten für Stillstandszeit')
    bars_rst = ax.bar(labels, kosten_rst, bottom=kosten_downtime, color='orange', label='Kosten durch Reststandzeit')

    # Werte oberhalb der Balken anzeigen
    for i, bar in enumerate(bars_rst):
        height = bar.get_height() + bars_downtime[i].get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f"{gesamt_kosten[i]:.2f} €",
                ha='center', va='bottom', fontsize=10)

    # Diagramm anpassen
    ax.set_title('Gesamtkosten mit Anteil der Stillstandszeit und Reststandzeit', fontsize=14)
    ax.set_ylabel('Kosten (€)', fontsize=12)
    ax.legend()


globale_ELF_nomaintenance = getELF1()
globale_ELF_planned = getELF2()
globale_ELF_predictive = getELF3()    

def zeige_alle_plots(globale_ELF_nomaintenance, globale_ELF_planned, globale_ELF_predictive):
    # Erstelle Subplots: 3 Reihen und 2 Spalten
    fig, axs = plt.subplots(3, 2, figsize=(15, 15))
    fig.subplots_adjust(wspace=0.3, hspace=0.3)

    # 1. Plot
    rst(globale_ELF_nomaintenance, globale_ELF_planned, globale_ELF_predictive, axs[0, 0])
    # 2. Plot
    vergleiche_type_prozent(axs[0, 1])
    # 3. und 4. Plot
    vergleiche_downtime(axs[1, 0], axs[1, 1])
    # 5. Plot
    vergleiche_kosten(axs[2, 0])

    vergleiche_kosten_reststandzeiten(axs[2,1])

    darstellung_gesamtkosten()

    # Leeren Subplot entfernen
    #fig.delaxes(axs[2, 1])
    plt.show()

zeige_alle_plots(globale_ELF_nomaintenance, globale_ELF_planned, globale_ELF_predictive)
