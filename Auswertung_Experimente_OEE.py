import sqlite3
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime
import math

# Datenbankpfade und Experimentnamen definieren
experimente = [
    {"pfad": "prod_data_no_maintenance.db", "name": "correctiv Maintenance"},
    {"pfad": "prod_data_planed_maintenance.db", "name": "planed Maintenance"},
    {"pfad": "prod_data_predictive_maintenance.db", "name": "predictive Maintenace"}
]

# Funktionen
def entferne_stillstandszeiten(row):
    """
    Zieht für jeden Tag zwischen start_ruesten und ende_bearbeitung 6 Stunden (21600 Sekunden) ab,
    wenn die Produktionszeit mehrere Tage umfasst.
    """
    start_time = row['start_ruesten']
    end_time = row['ende_bearbeitung']
    
    if pd.isna(start_time) or pd.isna(end_time):
        return 0  # Rückgabe von 0 für ungültige Einträge
    
    # Berechne die Produktionszeit in Sekunden
    production_time = (end_time - start_time).total_seconds()
    
    # Berechne die Anzahl der Tage zwischen Start- und Endzeit
    days_diff = (end_time.date() - start_time.date()).days
    
    # Wenn die Zeitspanne mehrere Tage umfasst, für jeden Tag 6 Stunden abziehen
    if days_diff > 0:
        production_time -= (days_diff + 1) * 21600  # 6 Stunden pro Tag in Sekunden (einschließlich Start- und Endtag)

    return max(production_time, 0)  # Sicherstellen, dass keine negativen Werte zurückgegeben werden

def berechne_anzahl_tage(startzeiten, endzeiten):
    """
    Berechnet die Anzahl der Tage im Betrachtungszeitraum basierend auf den minimalen und maximalen Daten.
    """
    startdatum = min(startzeiten.min(), endzeiten.min())
    enddatum = max(startzeiten.max(), endzeiten.max())
    return (enddatum - startdatum).days

def berechne_oee_fuer_experiment(db_path):
    """
    Berechnet die OEE-Werte für ein Experiment basierend auf einer Datenbankverbindung.
    """
    verbindung = sqlite3.connect(db_path)

    # Daten laden
    flf_df = pd.read_sql_query("SELECT * FROM FLF", verbindung)
    auftraege_df = pd.read_sql_query("SELECT * FROM auftraege", verbindung)
    elf_df = pd.read_sql_query("SELECT * FROM ELF", verbindung)

    # Verbindung schließen
    verbindung.close()

    # Datenaufbereitung
    flf_df['Charge'] = flf_df['Charge'].astype(str)
    auftraege_df['Charge'] = auftraege_df['Charge'].astype(str)

    # Zeitspalten konvertieren
    elf_df['start_downtime'] = pd.to_datetime(elf_df['start_downtime'], errors='coerce')
    elf_df['end_downtime'] = pd.to_datetime(elf_df['end_downtime'], errors='coerce')
    flf_df['start_ruesten'] = pd.to_datetime(flf_df['start_ruesten'], errors='coerce')
    flf_df['ende_bearbeitung'] = pd.to_datetime(flf_df['ende_bearbeitung'], errors='coerce')

    # Produktionszeit anpassen
    flf_df['adjusted_production_time'] = flf_df.apply(entferne_stillstandszeiten, axis=1)

    # Verfügbare Zeit berechnen
    anzahl_tage = berechne_anzahl_tage(flf_df['start_ruesten'], flf_df['ende_bearbeitung'])
    gesamt_verfuegbare_zeit = 57600 * anzahl_tage  # 57.600 Sekunden pro Tag * Anzahl der Tage

    # Stillstandzeiten berechnen
    elf_df['downtime'] = (elf_df['end_downtime'] - elf_df['start_downtime']).dt.total_seconds().fillna(0)

    # OEE-Berechnungen
    production_time_per_machine = flf_df.groupby('bmg')['adjusted_production_time'].sum()
    downtime_per_machine = elf_df.groupby('bmg')['downtime'].sum().reindex(flf_df['bmg'].unique(), fill_value=0)
    availabel_time = gesamt_verfuegbare_zeit - downtime_per_machine

    availability_per_machine = (availabel_time / gesamt_verfuegbare_zeit).fillna(0)
    flf_df['good_parts'] = flf_df['anzahl_bauteile'] - flf_df['ausschuss']
    quality_per_machine = (flf_df.groupby('bmg')['good_parts'].sum() / flf_df.groupby('bmg')['anzahl_bauteile'].sum()).fillna(0)
    performance_per_machine = (production_time_per_machine / availabel_time).fillna(0)

    oee_per_machine = (availability_per_machine * performance_per_machine * quality_per_machine).fillna(0)

    oee_per_machine = oee_per_machine[oee_per_machine > 0]

    return oee_per_machine

# OEE-Berechnungen für alle Experimente
oee_ergebnisse = [(experiment["name"], berechne_oee_fuer_experiment(experiment["pfad"])) for experiment in experimente]

# Diagrammerstellung
total_plots = len(oee_ergebnisse)  # Ein Diagramm pro Experiment

rows = math.ceil(total_plots / 2)
fig, axs = plt.subplots(rows, 2, figsize=(15, 5 * rows))
fig.tight_layout(pad=5.0)

# Flache Liste der Achsen für einfachere Zuordnung
axs = axs.flatten()

for i, (experiment_name, oee_per_machine) in enumerate(oee_ergebnisse):
    axs[i].bar(oee_per_machine.index, oee_per_machine.values, color='skyblue', edgecolor='black')
    axs[i].set_title(f"OEE pro Maschine ({experiment_name})")
    axs[i].set_xlabel("Maschine")
    axs[i].set_ylabel("OEE (%)")
    axs[i].set_ylim(0, 1)

    # Hinzufügen von Text für die OEE-Werte
    for bar in axs[i].patches:
        height = bar.get_height()
        axs[i].text(bar.get_x() + bar.get_width() / 2, height, f'{height:.2f}', ha='center', va='bottom', fontsize=10)

# Überflüssige Achsen entfernen
for ax in axs[len(oee_ergebnisse):]:
    ax.remove()

plt.show()
