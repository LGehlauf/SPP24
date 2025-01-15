import sqlite3
import pandas as pd



# returns a dict containing the total driven distance and the driven distance while empty of each ffz
# also the total mean waiting time from all charges as a difference of "ende bearbeitung" and "abtransport"  
def calc_KPIs(path_to_db: str) -> dict:
    TLF = getTLF(path_to_db)
    singleDistances = { key : 
        {
            'TotalDistance' : value['KumTotalDistance'].max(), 
            'EmptyDistance': value['KumEmptyDistance'].max()
        }
        for key, value in TLF.items()
    }

    globalTotalDistance = sum(item['TotalDistance'] for item in singleDistances.values())
    globalEmptyDistance = sum(item['EmptyDistance'] for item in singleDistances.values())
    

    FLF = getFLF(path_to_db)
    
    meanWaitingTime = FLF['wartezeit'].mean()


    Dict = {
        'globalTotalDistance' : globalTotalDistance,
        'globalEmptyDistance': globalEmptyDistance,
        'SingleDistances': singleDistances,
        'globalMeanWaitingTime': meanWaitingTime
    }

    return Dict


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


def getTLF(path_to_db: str) -> dict:
    con = sqlite3.connect(path_to_db)
    TLF = pd.read_sql_query("SELECT * FROM TLF", con)
    con.close()
    TLF['startzeitpunkt'] = pd.to_datetime(TLF['startzeitpunkt'], format='mixed', errors='raise')
    TLF['endzeitpunkt'] = pd.to_datetime(TLF['endzeitpunkt'], format='mixed', errors='raise')
    
    TLF['Distance'] = TLF['route'].apply(calc_distances)
    TLF['KumTotalDistance'] = TLF.groupby('FFZ_id')['Distance'].cumsum()

    TLF['KumEmptyDistance'] = TLF.groupby('FFZ_id').apply(
        lambda FFZ_id: FFZ_id.loc[FFZ_id['charge'].isna(), 'Distance'].cumsum()
    ).reset_index(level = 0, drop = True)

    
    nTLF = {key: gruppe_df for key, gruppe_df in TLF.groupby('FFZ_id') }
    #for key, tlf in nTLF.items():
    #    print(key, tlf, sep="\n")

    return nTLF

def getFLF(path_to_db: str) -> dict:
    con = sqlite3.connect(path_to_db)
    raw = pd.read_sql_query("SELECT * FROM FLF", con)
    con.close()
    FLF = pd.DataFrame()
    
    FLF['ende_bearbeitung'] = pd.to_datetime(raw['ende_bearbeitung'], format='mixed', errors='raise')
    FLF['abtransport'] = pd.to_datetime(raw['abtransport'], format='mixed', errors='raise')
    FLF = FLF.dropna(subset=['abtransport', 'ende_bearbeitung'])
    FLF['wartezeit'] = FLF['abtransport'] - FLF['ende_bearbeitung']
    FLF['wartezeit'] = FLF.apply(adjust_diff, axis=1)
    
    # print(FLF)

    return FLF 

def adjust_diff(row):
    days_diff = (row['abtransport'].date() - row['ende_bearbeitung'].date()).days
    adjusted_diff = row['wartezeit']
    if days_diff > 0:
        adjusted_diff -= pd.Timedelta(hours=8) 
        adjusted_diff -= pd.Timedelta(days=days_diff - 1) 
    return adjusted_diff

if __name__ == "__main__":
    KPIs = calc_KPIs("prod_data_no_maintenance.db")
a = 0