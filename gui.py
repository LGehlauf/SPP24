import sqlite3
import pygame
import sys
from datetime import datetime, timedelta
import re
import math
import os
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from collections import defaultdict



# to do: auslastung der fahrzeuge, anteil an leerfahrten (zb pro Schicht), zurückgelegter Weg
# fkt mit start und endzeitpunkt -> diagramm

Lines = [   {'StartEnd': ['a', 'c'], 'Distance': 15},
            {'StartEnd': ['a', 'b'], 'Distance': 11},
            {'StartEnd': ['a', 'd'], 'Distance': 16},
            {'StartEnd': ['c', 'g'], 'Distance': 12},
            {'StartEnd': ['c', 'b'], 'Distance': 6},
            {'StartEnd': ['b', 'd'], 'Distance': 5},
            {'StartEnd': ['d', 'e'], 'Distance': 17},
            {'StartEnd': ['g', 'e'], 'Distance': 6},
            {'StartEnd': ['e', 'f'], 'Distance': 14}
]

class BMG:
    def __init__(self, ShortName, Abbreviation, Pos, LongName, Size=(50,50), Lager=False):
        self.ShortName = ShortName
        self.Abbreviation = Abbreviation
        self.LongName = LongName
        self.Pos = Pos
        self.Size = Size
        # left, top, width, height
        self.main = (self.Pos[0] - 0.5 * self.Size[0], self.Pos[1] - 0.5 * self.Size[1], self.Size[0], self.Size[1])
        self.pre = (self.main[0] - 1.2 * self.main[2], self.main[1] + 0.1 * self.main[3], 1.2 * self.main[2], 0.8 * self.main[3])
        self.post = (self.main[0] + self.main[2], self.pre[1], self.pre[2], self.pre[3])
        self.wrapper = (self.pre[0] - 10, self.main[1] - 40, self.pre[2] + self.main[2] + self.post[2] + 20, self.main[3] + 100)
        self.Lager = Lager
        self.carsQueued = 0
        self.label_text = f"{self.LongName} ({self.Abbreviation}), Q: {self.carsQueued}"
        

    def draw(self, screen, font):
        label = font.render(self.label_text, True, (0,0,0))
        label_rect = label.get_rect(center=(self.Pos[0], self.main[1] - 0.5 * self.main[3]))
        screen.blit(label, label_rect)
        self.Rect = pygame.draw.rect(screen, (0, 0, 0), self.wrapper, width=1, border_radius=10)
        self.Stations = (self.Rect.midleft, self.Rect.midtop, self.Rect.midright, self.Rect.midbottom)
        # for station in self.Stations:
        #     pygame.draw.circle(screen, (30,30,30), station, 5)
        if not self.Lager:
            pygame.draw.rect(screen, (0, 0, 0), self.main, width=1, border_radius=10)
            pygame.draw.rect(screen, (0, 0, 0), self.pre, width=1, border_radius=5)
            pygame.draw.rect(screen, (0, 0, 0), self.post, width=1, border_radius=5)

    def carQueue(self, screen, font):
        offset = self.carsQueued * 4



# RTL = BMG('RTL', 'a', (100, 300), 'Rohteillager', Lager=True)
# SAE = BMG('SAE', 'b', (500, 300), 'Sägen')
# DRH = BMG('DRH', 'c', (500, 100), 'Drehen')
# FRA = BMG('FRA', 'd', (500, 500), 'Fräsen')
# QPR = BMG('QPR', 'e', (900, 300), 'Qualitätsprüfung')
# FTL = BMG('FTL', 'f', (1300, 300), 'Fertigteillager', Lager=True)
# LFF = BMG('LFF', 'g', (900, 100), 'Ladestation FFZ', Lager=True)

# BMGen = [RTL, SAE, DRH, FRA, QPR, FTL, LFF]

BMGen = [
    BMG('RTL', 'a', (100, 300), 'Rohteillager', Lager=True),
    BMG('SAE', 'b', (500, 300), 'Sägen'),
    BMG('DRH', 'c', (500, 100), 'Drehen'),
    BMG('FRA', 'd', (500, 500), 'Fräsen'),
    BMG('QPR', 'e', (900, 300), 'Qualitätsprüfung'),
    BMG('FTL', 'f', (1300, 300), 'Fertigteillager', Lager=True),
    BMG('LFF', 'g', (900, 100), 'Ladestation FFZ', Lager=True)
]


def parse_datetime(datums_string:str):
    for format in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(datums_string, format)
        except TypeError:
            return None
        except ValueError:
            continue
    raise ValueError(f"Datumsformat von '{datums_string}' ist unbekannt")

def parse_route(route_string:str) -> list[tuple]:
    matches = re.findall(r"([a-z])", route_string)
    return tuple(matches)

def getTLF(cur):
    cur.execute("SELECT * FROM TLF")
    raw = cur.fetchall()
    # keys = ['VorgangsNr', 'FFZ_ID', 'Startknoten', 'Endknoten', 'Route', 'Startzeitpunkt', 'Endzeitpunkt', 'Akkustand', 'Charge']    
    keys = ['VNR', 'FFZ_ID', 'SK', 'EK', 'Route', 'SZP', 'EZP', 'Akkustand', 'Charge']
    TLF = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        Dict['SZP'] = parse_datetime(Dict['SZP'])
        Dict['EZP'] = parse_datetime(Dict['EZP'])
        Dict['Route'] = parse_route(Dict['Route'])
        TLF.append(Dict)
    return TLF

def getFLF(cur):
    cur.execute("SELECT * FROM FLF")
    raw = cur.fetchall()
    #keys = ['Charge', 'BMG', 'Ankunft', 'Start_Ruesten', 'Start_Bearbeitung', 'Ende_Bearbeitung', 'Abtransport', 'Anzahl_Bauteile', 'Ausschuss']
    keys = ['Ch', 'BMG', 'AnZP', 'RZP', 'SB', 'EB', 'AbZP', 'Anz_Bauteile', 'Ausschuss'] # BAUSTELLE
    FLF = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        for key in ['AnZP', 'RZP', 'SB', 'EB', 'AbZP']:
            #try:
            Dict[key] = parse_datetime(Dict[key])
            # except:
            #     pass
        # Dict['AnZP'] = parse_datetime(Dict['AnZP'])
        # Dict['RZP'] = parse_datetime(Dict['RZP'])
        # Dict['SB'] = parse_datetime(Dict['SB'])
        # Dict['EB'] = parse_datetime(Dict['EB'])
        # Dict['AbZP'] = parse_datetime(Dict['AbZP'])
        FLF.append(Dict)
    return FLF
    

def PyGameDrawClock(screen, font, clockExtern, fps):
    text = f"{clockExtern.strftime("%d. %B %Y %H:%M")}"
    PyGameWrite(screen, font, text, (600, 600), 'top')
    # text = f"FPS: {round(fps,1)}"
    # PyGameWrite(screen, font, text, (1100, 700), 'left')

def PyGameSampleCurrMovements(TLF, time, currMovements):
    for mov in currMovements:
        if mov['EZP'] < time: 
            currMovements.remove(mov)
    for line in TLF:
        if line['SZP'] <= time and line['EZP'] > time: # Start liegt in der Vergangenheit, Ende aber in der Zukunft -> aktuell
            line['PyRoute'] = None
            TLF.remove(line)
            currMovements.append(line)
        if line['EZP'] > time:
            break
    return currMovements


def TLFAddWaits(rawTLF):
    # ###################### workaround error
    # TLF = []
    # for line in rawTLF:
    #     if line['VNR'] > 816:
    #         TLF.append(line)
    # ###################### workaround error

    splits = defaultdict(list)
    for line in TLF:
        splits[line['FFZ_ID']].append(line)

    for key in splits: # split ist nicht das element sondern der key
        for i in range(len(splits[key]) - 1):
            thisLine = splits[key][i]
            nextLine = splits[key][i+1]    
            # gibt es eine zeitliche Lücke zwischen Start- und Endzeitpunkt der Fahrten?
            if thisLine['EZP'] < nextLine['SZP']: 
                # print(f'{key} waits between {thisLine['VNR']} and {nextLine['VNR']} from {thisLine['EZP']} to {nextLine['SZP']}')
                splits[key].append({'VNR':'x', 'FFZ_ID':thisLine['FFZ_ID'],
                                'SK': thisLine['EK'], 'EK': thisLine['EK'],
                                'SZP': thisLine['EZP'],
                                'EZP': nextLine['SZP']})
            if thisLine['EZP'] > nextLine['SZP']: # negative Zeit!
                splits[key].append({'VNR':'negT', 'FFZ_ID':thisLine['FFZ_ID'],
                                'SK': thisLine['EK'], 'EK': nextLine['SK'],
                                'SZP': thisLine['EZP'],
                                'EZP': nextLine['SZP']})                
            if thisLine['EK'] != nextLine['SK']: # teleport!!
                # raise AssertionError(f'{key} teleported between {thisLine['VNR']} and {nextLine['VNR']} from {thisLine['EK']} to {nextLine['SK']}')
                splits[key].append({'VNR':'t', 'FFZ_ID':thisLine['FFZ_ID'],
                                'SK': thisLine['EK'], 'EK': nextLine['SK'],
                                'SZP': thisLine['EZP'],
                                'EZP': nextLine['SZP']})                
    combined_list = [item for sublist in splits.values() for item in sublist]
    sorted_list = sorted(combined_list, key=lambda x: x['SZP'])
    a = 0

    return sorted_list


def calcDistanceRatio(Route):
    cumuDistances = []
    cumuDistances.append(0)
    Sum = 0
    for i in range(len(Route) - 1):
        for line in Lines:
            if Route[i] in line['StartEnd'] and Route[i+1] in line['StartEnd']:
                cumuDistances.append(line['Distance'] + cumuDistances[-1])
                Sum += line['Distance']
                break
    return tuple(distance / Sum for distance in cumuDistances)
    

def viridis_to_rgb(fraction, total):
    value = fraction / total
    cmap = plt.get_cmap('viridis')
    rgb = cmap(value)[:3]
    rgb_255 = tuple(int(x * 255) for x in rgb)
    return rgb_255

def PyGameDrawChargen(screen, font, currMovements, time):
    for mov in currMovements:
        if mov :
            pass


def PyGameDrawCars(screen, font, currMovements, time, FFZ):
    width, height = 16, 16
    for mov in currMovements:
        if mov['VNR'] != 'x':
            if mov['PyRoute'] == None: # only executed once per movement
                mov['PyRoute'] = PyGameFindConnections(mov) # jetzt sind die zu fahrenden koordinaten bekannt
                mov['DistanceRatio'] = calcDistanceRatio(mov['Route']) # 
                mov['TravelTime'] = mov['EZP'] - mov['SZP']
                checkpointTimes = []
                for ratio in mov['DistanceRatio']:
                    checkpointTimes.append(mov['SZP'] + ratio * mov['TravelTime'])    
                mov['CheckpointTimes'] = checkpointTimes
        
            for i in range(len(mov['Route']) - 1):
                # welche strecke muss genau jetzt animiert werden? Dafür gibt es die CheckpointTimes
                if time > mov['CheckpointTimes'][i] and time < mov['CheckpointTimes'][i+1]:
                    DistanceX = mov['PyRoute'][i][1][0] - mov['PyRoute'][i][0][0]
                    DistanceY = mov['PyRoute'][i][1][1] - mov['PyRoute'][i][0][1]
                    TimeRatio = (time - mov['CheckpointTimes'][i]) / (mov['CheckpointTimes'][i+1] - mov['CheckpointTimes'][i])
                    PosX = mov['PyRoute'][i][0][0] + TimeRatio * DistanceX
                    PosY = mov['PyRoute'][i][0][1] + TimeRatio * DistanceY
                    rect = (PosX - width * 0.5, PosY - height * 0.5, width, height)
                    colour = viridis_to_rgb(int(mov['FFZ_ID'][-1]), len(FFZ))
                    Rect = pygame.draw.rect(screen, colour, rect, border_radius=2)
                    if mov['Charge'] != None: 
                        pygame.draw.circle(screen, (255,0,0), (PosX, PosY), 5, 5)
                    # offset = int(mov['FFZ_ID'][-1]) * 20 
                    # text = f"trying {mov['FFZ_ID']} [{mov['Route'][i]} -> {mov['Route'][i+1]}]"
                    # PyGameWrite(screen, font, text, (200, 700 + offset), 'left')
                    try:
                        text = f"{mov['FFZ_ID']} -> {mov['EK']}"
                        PyGameWrite(screen, font, text, Rect.midtop, 'bottom')
                    except:
                        pass

        else: # current movement is waiting
            offset = int(mov['FFZ_ID'][-1]) * 22
            WS = next((bmg for bmg in BMGen if bmg.Abbreviation == mov['SK']), None) # Waiting Station
            rect = (WS.wrapper[0] + 20 + offset, WS.wrapper[1] + WS.wrapper[3] - 20, width, height)
            colour = viridis_to_rgb(int(mov['FFZ_ID'][-1]), len(FFZ))
            Rect = pygame.draw.rect(screen, colour, rect, border_radius=2)


def findShortestPath(stations1, stations2):
    min_distanz = float('inf')
    bestes_paar = None
    for (x1, y1) in stations1:
        for (x2, y2) in stations2:
            distanz = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            if distanz < min_distanz:
                min_distanz = distanz
                bestes_paar = ((x1, y1), (x2, y2))
    return bestes_paar

def PyGameFindConnections(movement):
    PyRoute = []
    for i in range(len(movement['Route'])):
        if i == len(movement['Route']) - 1:
            break
        start = next((bmg for bmg in BMGen if bmg.Abbreviation == movement['Route'][i]), None)
        end = next((bmg for bmg in BMGen if bmg.Abbreviation == movement['Route'][i+1]), None)

        bestes_paar = findShortestPath(start.Stations, end.Stations)
        PyRoute.append(bestes_paar)
    return tuple(PyRoute)

def PyGameWrite(screen, font, text, Pos, LRTD):
    label = font.render(text, True, (0,0,0))
    if (LRTD == 'left'): label_rect = label.get_rect(midleft=Pos)
    if (LRTD == 'right'): label_rect = label.get_rect(midright=Pos)
    if (LRTD == 'top'): label_rect = label.get_rect(midtop=Pos)
    if (LRTD == 'bottom'): label_rect = label.get_rect(midbottom=Pos)
    screen.blit(label, label_rect)

def initPygame(stations:list[dict], lines:list[dict], TLF:list[dict]) -> None:
    FFZ = {row['FFZ_ID'] for row in TLF} # set of used FFZ
    pygame.init()
    screen = pygame.display.set_mode((1400, 800))
    clock = pygame.time.Clock()
    framerate = 60 # fps
    dirPath = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
    fontPath = dirPath + '/SourceSans3-Regular.ttf'
    font = pygame.font.Font(fontPath, 14)
    
    Time = TLF[0]['SZP'] - timedelta(minutes=1)
    passedTime = 0

    currMovements = []
    # carList = []
    # for car in cars:
    #     carList.append(pygame.Rect(100, 100, 20, 20))
    states = ['unpause', 'pause']
    state = 0
    # SimSpeeds = [-32, -16, -8, -4, -2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 4, 8, 16, 32]
    SimSpeeds = [0.25, 0.5, 1, 2, 4, 8, 16, 32]
    SimSpeed = 3
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    state += 1
                    if state == 2: state = 0                        
                if event.key == pygame.K_UP:
                    SimSpeed += 1
                    if SimSpeed > len(SimSpeeds) - 1: SimSpeed = len(SimSpeeds) - 1
                if event.key == pygame.K_DOWN:
                    SimSpeed -= 1
                    if SimSpeed == -1: SimSpeed = 0

        screen.fill((255, 255, 255))

        for bmg in BMGen:
            bmg.draw(screen, font)

        if states[state] == 'pause':
            Time = Time
        elif states[state] == 'unpause':
            Time += timedelta(milliseconds=passedTime) * 100 * SimSpeeds[SimSpeed]
            passedTime = clock.get_time()

        fps = clock.get_fps()
        PyGameDrawClock(screen, font, Time, fps)

        currMovements = PyGameSampleCurrMovements(TLF, Time, currMovements)

        PyGameWrite(screen, font, f'Simulation speed: {SimSpeeds[SimSpeed]}', (10, 500), 'left')

        i = 0
        for key in ['VNR', 'FFZ_ID', 'SK', 'EK', 'SZP', 'EZP']:
            PyGameWrite(screen, font, key, (10 + i * 50, 650), 'left')
            i += 1

        for j, mov in enumerate(currMovements):
            i = 0
            for key, value in mov.items():
                if key in ['VNR', 'FFZ_ID', 'SK', 'EK', 'SZP', 'EZP']:
                    if key in ['SZP', 'EZP']:
                        val = value.strftime('%H:%M')
                        PyGameWrite(screen, font, str(val), (10 + i * 50, 670 + j * 20), 'left')   
                    else: PyGameWrite(screen, font, str(value), (10 + i * 50, 670 + j * 20), 'left')
                    i += 1

        PyGameDrawCars(screen, font, currMovements, Time, FFZ)
        
        pygame.display.flip()
        clock.tick(framerate)

con = sqlite3.connect('prod_data.db')
cur = con.cursor()

TLF = getTLF(cur)
FLF = getFLF(cur)


modifiedTLF = TLFAddWaits(TLF)




a =0


initPygame(BMGen, Lines, modifiedTLF)

con.close()
