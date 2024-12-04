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


startzeitpunkt =    datetime.strptime("2020-10-01 18:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")
endzeitpunkt =      datetime.strptime("2024-10-10 18:00:00.000000", "%Y-%m-%d %H:%M:%S.%f")


def getTLF():
    con = sqlite3.connect("prod_data.db")
    TLF = pd.read_sql_query("SELECT * FROM TLF", con)
    TLF['startzeitpunkt'] = pd.to_datetime(TLF['startzeitpunkt'], format='mixed', errors='raise')
    TLF['endzeitpunkt'] = pd.to_datetime(TLF['endzeitpunkt'], format='mixed', errors='raise')
    TLF = TLF[TLF['startzeitpunkt'].between(startzeitpunkt, endzeitpunkt, inclusive='both')] # only in given timeframe!
    # a = 0
    return TLF
    
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


def drawPlots():
    rows = 2
    columns = 3# AuswTLF.len()
    fig, axes = plt.subplots(nrows=rows, ncols = columns, figsize = (3 * columns, 3 * rows))
    for ax in axes.ravel():
        ax.pie(Aus)
    a = 0

TLF = getTLF()
TLF['Distance'] = TLF['route'].apply(calc_distances)

b =  TLF.groupby('FFZ_id') 

nTLF = {key: gruppe_df for key, gruppe_df in TLF.groupby('FFZ_id') }

AuswTLF = {key: {
    'fahrten': None, 
    'leerfahrten': None,
    'gesamter_weg': None,
    'leerweg': None
    } for key, _ in nTLF.items()}

for key, ffzTLF in nTLF.items():
    print(key)
    AuswTLF[key]['fahrten'] = ffzTLF.shape[0]
    AuswTLF[key]['leerfahrten'] = ffzTLF['charge'].isnull().sum()
    AuswTLF[key]['gesamter_weg'] = ffzTLF['Distance'].sum()
    AuswTLF[key]['leerweg'] = ffzTLF.loc[ffzTLF['charge'].notna(), 'Distance'].sum()
    
    print()
    
drawPlots()


#print(TLF.loc[339,:])


a= 0
