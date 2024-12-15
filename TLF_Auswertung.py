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


# to do: auslastung der fahrzeuge, anteil an leerfahrten (zb pro Schicht), zurückgelegter Weg
# fkt mit start und endzeitpunkt -> diagramm


startzeitpunkt =    datetime.strptime("2024-01-01 06:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
endzeitpunkt =      datetime.strptime("2024-01-03 23:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")


def getTLF():
    con = sqlite3.connect("prod_data.db")
    TLF = pd.read_sql_query("SELECT * FROM TLF", con)
    TLF['startzeitpunkt'] = pd.to_datetime(TLF['startzeitpunkt'], format='mixed', errors='raise')
    TLF['endzeitpunkt'] = pd.to_datetime(TLF['endzeitpunkt'], format='mixed', errors='raise')
    TLF = TLF[TLF['startzeitpunkt'].between(startzeitpunkt, endzeitpunkt, inclusive='both')] # only in given timeframe!
    # a = 0
    TLF['Distance'] = TLF['route'].apply(calc_distances)
    # print(TLF.groupby('FFZ_id').head())
    TLF['KumDistance'] = TLF.groupby('FFZ_id')['Distance'].cumsum()
    aTLF = TLF.drop('endzeitpunkt', axis='columns')
    bTLF = TLF.drop('startzeitpunkt', axis='columns')

    aTLF['Aktion'] = "start"
    aTLF = aTLF.rename(columns= {'startzeitpunkt': 'zeitpunkt'})
    aTLF['KumDistance'] = aTLF['KumDistance'] - aTLF['Distance']
    bTLF['Aktion'] = "ende"
    bTLF = bTLF.rename(columns= {'endzeitpunkt': 'zeitpunkt'})

    TLF = pd.concat([aTLF, bTLF])
    TLF = TLF.sort_values(by=["zeitpunkt", 'Aktion']) # sortiert erst nach zeitpunkt, dass nach aktion (also ['start', 'ende']), ende soll vor anfang kommen und ist alphabetisch vor start (zum glück)
    
    TLF = TLF.head(100)

    # print(TLF.head(n=20))
    # print(aTLF.head())
    
    nTLF = {key: gruppe_df for key, gruppe_df in TLF.groupby('FFZ_id') }
    for key, tlf in nTLF.items():
        print(key, tlf, sep="\n")

    return nTLF
    
def calc_distances(route):    
    Distances = {
        ('a', 'c'): 70,
        ('a', 'b'): 60,
        ('a', 'd'): 75,
        ('c', 'g'): 40,
        ('c', 'b'): 25,
        ('b', 'd'): 45,
        ('d', 'e'): 85,
        ('g', 'e'): 30,
        ('e', 'f'): 85,
        ('g', 'h'): 45,
        ('e', 'h'): 55
    }

    for (start, ziel), distanz in list(Distances.items()): # hin und zurück ...
        Distances[(ziel, start)] = distanz

    punkte = route.split("->")
    strecken = [(punkte[i], punkte[i+1]) for i in range(len(punkte)-1)]
    return sum(Distances.get(strecke, 0) for strecke in strecken)


def drawPlots(AuswTLF):
    cmap = cm.get_cmap('viridis')
    colors = cmap([0.4, 1.0])
    rows = 3
    columns = len(AuswTLF)
    fig, axes = plt.subplots(nrows=rows, ncols = columns, figsize = (3 * columns, 1.5 * rows))
    axes = axes.flatten()
    
    

    for col_idx, (ffz, categories) in enumerate(AuswTLF.items()):
        
        labels = list(categories.keys())
        values = list(categories.values())
    
        axes[col_idx].set_title(f"{ffz} - Fahrten")
        axes[col_idx].pie([values[0], values[1]], labels=[labels[0], labels[1]], autopct='%1.1f%%', colors=colors)
        
        # Zweites Piechart (Zeile 2)
        axes[col_idx + columns].set_title(f"{ffz} - Wege")
        axes[col_idx + columns].pie([values[2], values[3]], labels=[labels[2], labels[3]], autopct='%1.1f%%', colors=colors)

        # colors = ['red' if pd.isna(value) else 'blue' for value in nTLF[key]['charge']] 
        x = nTLF[ffz]['zeitpunkt'].to_numpy()
        y = nTLF[ffz]['KumDistance'].to_numpy()
        z = pd.to_numeric(nTLF[ffz]['charge'], errors='coerce').to_numpy()
        is_nan = np.isnan(z)
        axes[col_idx + 2 * columns].set_title(f"{ffz} - Strecke")
        axes[col_idx + 2 * columns].plot(x, np.where(is_nan, np.nan, y), color = colors[0])
        axes[col_idx + 2 * columns].plot(x, np.where(is_nan, y, np.nan), color = colors[1])
        locator = mdates.AutoDateLocator(maxticks=5, minticks=3)
        formatter = mdates.DateFormatter("%H:%M")
        axes[col_idx + 2 * columns].xaxis.set_major_locator(locator)
        axes[col_idx + 2 * columns].xaxis.set_major_formatter(formatter)
        

        # Titel für das gesamte Diagramm
    
    plt.suptitle(f"start:  {startzeitpunkt} \nende: {endzeitpunkt}", fontsize=14)

    # Layout anpassen
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Platz für den Titel lassen
    # plt.get_current_fig_manager().full_screen_toggle()
    plt.show()

    a = 0




nTLF = getTLF()

AuswTLF = {key: {
    'lastfahrten': None, 
    'leerfahrten': None,
    'lastweg': None,
    'leerweg': None
    } for key, _ in nTLF.items()}

for key, ffzTLF in nTLF.items():
    # print(key)
    AuswTLF[key]['lastfahrten'] = ffzTLF['charge'].notnull().sum()
    AuswTLF[key]['leerfahrten'] = ffzTLF['charge'].isnull().sum()
    AuswTLF[key]['lastweg'] = ffzTLF.loc[ffzTLF['charge'].notnull(), 'Distance'].sum()
    AuswTLF[key]['leerweg'] = ffzTLF.loc[ffzTLF['charge'].isnull(), 'Distance'].sum()
    # print(ffzTLF.loc[ffzTLF['charge'].notnull(), 'Distance'])
    # print()
    
a = 0

drawPlots(AuswTLF)


#print(TLF.loc[339,:])


a= 0
