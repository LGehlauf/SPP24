#Dashboard
import numpy as np
import sqlite3
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime
import matplotlib.dates as mdates
from matplotlib.dates import date2num
import matplotlib.patches as patches
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def Dashboard():
    # Verbindung zur Datenbank herstellen
    db_path = "prod_data.db"
    verbindung = sqlite3.connect(db_path)

    # Maschinen dynamisch aus der Datenbank abrufen
    maschinen_query = "SELECT DISTINCT bmg FROM FLF WHERE bmg not in ('RTL', 'FTL')"
    maschinen = pd.read_sql_query(maschinen_query, verbindung)['bmg'].tolist()

    # Varianten dynamisch aus der Datenbank abrufen
    varianten_query = "SELECT DISTINCT id FROM auftraege"
    varianten = pd.read_sql_query(varianten_query, verbindung)['id'].tolist()

    # Daten aus der Datenbank abrufen
    flf_df = pd.read_sql_query("SELECT * FROM FLF", verbindung)
    auftraege_df = pd.read_sql_query("SELECT * FROM auftraege", verbindung)
    elf_df = pd.read_sql_query("SELECT * FROM ELF", verbindung)
    arbeitsplaene_df = pd.read_sql_query("SELECT * FROM arbeitsplaene",verbindung)

    # Daten aufbereiten
    flf_df['Charge'] = flf_df['Charge'].astype(str)
    auftraege_df['Charge'] = auftraege_df['Charge'].astype(str)

    auftraege_df = auftraege_df.merge(flf_df[['Charge', 'bmg']], on='Charge', how='inner')

    # Nur relevante Maschinen und Varianten
    auftraege_df = auftraege_df[auftraege_df['bmg'].isin(maschinen)]
    elf_df = elf_df[elf_df['bmg'].isin(maschinen)]
    flf_df = flf_df[flf_df['bmg'].isin(maschinen)]

    # Zeitspalten konvertieren
    auftraege_df['freigabe'] = pd.to_datetime(auftraege_df['freigabe'], format="%Y-%m-%d %H:%M:%S",errors='coerce')
    auftraege_df['fertigstellung'] = pd.to_datetime(auftraege_df['fertigstellung'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    elf_df['start_downtime'] = pd.to_datetime(elf_df['start_downtime'], format="%Y-%m-%d %H:%M:%S", errors='coerce')
    elf_df['end_downtime'] = pd.to_datetime(elf_df['end_downtime'], format="%Y-%m-%d %H:%M:%S", errors='coerce')

    # Produktionszeit und Downtime berechnen
    auftraege_df['production_time'] = (auftraege_df['fertigstellung'] - auftraege_df['freigabe']).dt.total_seconds().fillna(0)
    # Planzeiten hinzufügen

    # Function to check if a weekend falls between two dates
    def subtract_weekend_time(row):
        start = row['freigabe']
        end = row['fertigstellung']
        
        # Initialize total_seconds as the raw difference
        if pd.isna(start) or pd.isna(end):  # Handle NaT cases
            return np.nan
        
        total_seconds = (end - start).total_seconds()

        # Check if there's a weekend in the date range
        days_range = pd.date_range(start=start, end=end, freq='D')  # Generate dates between
        has_weekend = any(day.weekday() in [5, 6] for day in days_range)  # Saturday=5, Sunday=6

        # Subtract 48 hours (in seconds) if weekend falls in the range
        if has_weekend:
            total_seconds -= 48 * 3600  # 48 hours in seconds

        return total_seconds

    # Apply the function to your DataFrame
    auftraege_df['adjusted_production_time'] = auftraege_df.apply(subtract_weekend_time, axis=1)

    arbeitsplaene_df['planzeit'] = ((arbeitsplaene_df['r_plan'] + (arbeitsplaene_df['t_plan']*auftraege_df['stueckzahl_plan'])))
    planzeit_pro_variante = arbeitsplaene_df.groupby('id')['planzeit'].sum()

    # Planzeiten den Aufträgen zuordnen
    auftraege_df = auftraege_df.merge(planzeit_pro_variante, on='id', how='left')


    elf_df['downtime'] = (elf_df['end_downtime'] - elf_df['start_downtime']).dt.total_seconds().fillna(0)

    # OEE-Berechnungen
    production_time_per_machine = auftraege_df.groupby('bmg')['production_time'].sum()
    downtime_per_machine = elf_df.groupby('bmg')['downtime'].sum()
    downtime_per_machine = downtime_per_machine.reindex(maschinen, fill_value=0)
    availability_per_machine = (production_time_per_machine / (production_time_per_machine + downtime_per_machine)).fillna(0)

    flf_df['good_parts'] = flf_df['anzahl_bauteile'] - flf_df['ausschuss']
    quality_per_machine = (flf_df.groupby('bmg')['good_parts'].sum() / flf_df.groupby('bmg')['anzahl_bauteile'].sum()).fillna(0)

    auftraege_df['cycle_performance'] = auftraege_df['stueckzahl_ist'] / auftraege_df['stueckzahl_plan']
    performance_per_machine = auftraege_df.groupby('bmg')['cycle_performance'].mean()

    oee_per_machine = (availability_per_machine * performance_per_machine * quality_per_machine).fillna(0)

    # Ausschuss berechnen
    ausschuss = (flf_df.groupby('bmg')['anzahl_bauteile'].sum() - flf_df.groupby('bmg')['good_parts'].sum())

    # Variablen für Tortendiagramme vorbereiten
    gesamtstückzahl = auftraege_df['stueckzahl_ist'].sum()
    stückzahlen_pro_variante = auftraege_df.groupby('id')['stueckzahl_ist'].sum()
    ausschuss_gesamt = flf_df['ausschuss'].sum()
    gutteile_gesamt = gesamtstückzahl - ausschuss_gesamt

    # --- Dashboard ---
    import math

    # Gesamtanzahl der Diagramme
    total_plots = len(maschinen) + 2  # OEE + Ausschuss + Variantenverteilung + Maschinen-Histogramme

    # Anzahl der Zeilen für 2 Spalten
    rows = math.ceil(total_plots / 2)

    # Neues Subplot-Layout
    fig, axs = plt.subplots(rows, 2, figsize=(15, 5 * rows))
    fig.tight_layout(pad=5.0)

    # Flache Liste der Achsen für einfachere Zuordnung
    axs = axs.flatten()

    # OEE pro Maschine darstellen
    axs[0].bar(oee_per_machine.index, oee_per_machine.values, color='skyblue', edgecolor='black')
    for bar in axs[0].patches:
        height = bar.get_height()
        axs[0].text(bar.get_x() + bar.get_width() / 2, height, f'{height:.2f}', ha='center', va='bottom', fontsize=10)
    axs[0].set_title("OEE pro Maschine")
    axs[0].set_xlabel("Maschine")
    axs[0].set_ylabel("OEE (%)")
    axs[0].set_ylim(0, 1)

    # Tortendiagramm: Verteilung der Varianten
    axs[1].pie(stückzahlen_pro_variante, labels=stückzahlen_pro_variante.index, autopct='%1.1f%%', startangle=90)
    axs[1].set_title("Verteilung der gefertigten Varianten")

    # Tortendiagramm: Ausschussrate
    axs[2].pie([gutteile_gesamt, ausschuss_gesamt], labels=['Gutteile', 'Ausschuss'], autopct='%1.1f%%', startangle=90)
    axs[2].set_title("Ausschussrate")

    # Histogramme für Durchlaufzeiten (Maschinen-spezifisch)
    for idx, variante in enumerate(varianten):
        variante_data = auftraege_df[auftraege_df['id'] == variante]
        variante_data = variante_data[variante_data["fertigstellung"].notna()]
        if idx + 3 < len(axs):  # Verhindern, dass wir außerhalb des Achsenbereichs schreiben
            # Durchlaufzeit in Minuten umrechnen
            production_time_days = variante_data['adjusted_production_time'] / (60*60*24)
            axs[idx + 3].hist(production_time_days, bins=25, color='blue', edgecolor='black', alpha=0.7)

            # Mittelwert und Standardabweichung berechnen
            mean_time = production_time_days.mean()
            std_time = production_time_days.std()

            axs[idx + 3].axvline(mean_time, color='orange', linestyle='--', linewidth=1.5, label=f'Mittlere DLZ: {mean_time:.2f} [BKT]')
            axs[idx + 3].fill_betweenx([0, axs[idx + 3].get_ylim()[1]], mean_time - std_time, mean_time + std_time, 
                                    color='gray', alpha=0.3, label=f'\u03c3: {std_time:.2f} [BKT]')
            
            axs[idx + 3].set_title(f"Durchlaufzeit Verteilung für Variante {variante}")
            axs[idx + 3].set_xlabel("Durchlaufzeit [BKT]")  # Achsentitel angepasst
            axs[idx + 3].set_ylabel("Anzahl")
            axs[idx + 3].legend()


    # Entfernen von leeren Subplots
    for i in range(total_plots, len(axs)):
        fig.delaxes(axs[i])

    # Diagramme anzeigen
    plt.show()


def Plantafel(start_date, end_date):
    # Umwandlung der Eingabedaten (start und end) in datetime-Objekte
    start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
    end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

    # Verbindung zur Datenbank wiederherstellen
    conn = sqlite3.connect("prod_data.db")

        # Daten aus den relevanten Tabellen abrufen
    auftraege_query = """
    SELECT a.Charge, a.start_ruesten, a.abtransport, a.bmg
    FROM FLF AS a
    """
    auftraege_data = pd.read_sql_query(auftraege_query, conn)

    # Konvertierung der Zeitstempel in Datetime-Objekte
    auftraege_data['start_ruesten'] = pd.to_datetime(auftraege_data['start_ruesten'], format='%Y-%m-%d %H:%M:%S'   )
    auftraege_data['abtransport'] = pd.to_datetime(auftraege_data['abtransport'], format='%Y-%m-%d %H:%M:%S')

    # Schließen der Verbindung zur Datenbank
    conn.close()

    # Filterung der Daten basierend auf dem gegebenen Zeitraum
    filtered_data = auftraege_data[
        (auftraege_data['start_ruesten'] >= start_date) &
        (auftraege_data['abtransport'] <= end_date)
    ]
    
    # Sortieren der Daten nach Maschinen und Startzeit
    filtered_data = filtered_data.sort_values(by=['bmg', 'start_ruesten'])
    
    # Normierung der Chargen
    unique_charges = filtered_data['Charge'].unique()
    charge_mapping = {charge: idx for idx, charge in enumerate(unique_charges)}
    filtered_data['Charge_norm'] = filtered_data['Charge'].map(charge_mapping)
    
    # Farben für verschiedene Chargen definieren
    color_map = cm.get_cmap('tab20', len(unique_charges))
    charge_colors = {idx: mcolors.rgb2hex(color_map(i)) for i, idx in enumerate(charge_mapping.values())}
    
    # Berechnung der Stillstandszeiten
    idle_times = []
    for machine, group in filtered_data.groupby('bmg'):
        group = group.sort_values('start_ruesten')
        for i in range(len(group) - 1):
            current_end = group.iloc[i]['abtransport']
            next_start = group.iloc[i + 1]['start_ruesten']
            if current_end < next_start:  # Es gibt eine Lücke
                idle_times.append({
                    'bmg': machine,
                    'start_idle': current_end,
                    'end_idle': next_start
                })
    
    # Gantt-Diagramm erstellen
    fig, ax = plt.subplots(figsize=(12, 8))
    for i, row in filtered_data.iterrows():
        start = row['start_ruesten']
        end = row['abtransport']
        color = charge_colors[row['Charge_norm']]
        ax.barh(row['bmg'], date2num(end) - date2num(start), left=date2num(start),
                color=color, edgecolor='black', label=row['Charge_norm'] if row['Charge_norm'] not in ax.get_legend_handles_labels()[1] else "")
        # Normierte Charge in der Mitte der Balken hinzufügen
        ax.text(date2num(start) + (date2num(end) - date2num(start)) / 2, 
                row['bmg'],  # Vertikale Position basierend auf 'bmg'
                str(row['Charge_norm']), 
                ha='center', va='center', fontsize=8, color='black')
    
    # Stillstandszeiten hinzufügen (mit Schraffur)
    for idle in idle_times:
        start_idle = idle['start_idle']
        end_idle = idle['end_idle']
        # Höhe der Stillstandszeit anpassen
        height_factor = 0.7  # Wert kleiner als 1 macht den Block schmaler
        ax.barh(idle['bmg'], date2num(end_idle) - date2num(start_idle), 
                left=date2num(start_idle),
                color='darkgray', edgecolor='black', hatch='//', alpha=1, height=height_factor)
        ax.text(date2num(start_idle) + (date2num(end_idle) - date2num(start_idle)) / 2, 
                idle['bmg'],  # Vertikale Position basierend auf 'bmg'
                'DT', 
                ha='center', va='center', fontsize=8, color='black')
    
    # Achsen und Titel anpassen
    ax.set_xlim(start_date, end_date)
    ax.set_xlabel("Zeit")
    ax.set_ylabel("Maschinen")
    ax.set_title(f"Plantafel vom {start_date.strftime('%Y-%m-%d %H:%M:%S')} bis {end_date.strftime('%Y-%m-%d %H:%M:%S')}")
    ax.xaxis_date()
    fig.autofmt_xdate()
    
    # Legende hinzufügen
    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys(), title="Normierte Charge", loc='upper left', bbox_to_anchor=(1.05, 1))
    
    plt.tight_layout()
    plt.show()

