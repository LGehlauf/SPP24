import sqlite3
import pygame
import sys
from datetime import datetime, timedelta
import re
import math
import os
import matplotlib.pyplot as plt
import matplotlib.cm as cm


# to do: auslastung der fahrzeuge, anteil an leerfahrten (zb pro Schicht), zurückgelegter Weg

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
        self.wrapper = (self.pre[0] - 10, self.main[1] - 50, self.pre[2] + self.main[2] + self.post[2] + 20, self.main[3] + 90)
        self.label_text = f"{self.LongName} ({self.Abbreviation})"
        self.Lager = Lager
        self.StationDistance = 5

    def draw(self, screen, font):
        label = font.render(self.label_text, True, (0,0,0))
        label_rect = label.get_rect(center=(self.Pos[0], self.main[1] - 0.5 * self.main[3]))
        screen.blit(label, label_rect)
        self.Rect = pygame.draw.rect(screen, (0, 0, 0), self.wrapper, width=1, border_radius=10)
        self.Stations = (self.Rect.midleft, self.Rect.midtop, self.Rect.midright, self.Rect.midbottom)
        for station in self.Stations:
            pygame.draw.circle(screen, (30,30,30), station, 5)
        if not self.Lager:
            pygame.draw.rect(screen, (0, 0, 0), self.main, width=1, border_radius=10)
            pygame.draw.rect(screen, (0, 0, 0), self.pre, width=1, border_radius=5)
            pygame.draw.rect(screen, (0, 0, 0), self.post, width=1, border_radius=5)

RTL = BMG('RTL', 'a', (100, 300), 'Rohteillager', Lager=True)
SAE = BMG('SAE', 'b', (500, 300), 'Sägen')
DRH = BMG('DRH', 'c', (500, 100), 'Drehen')
FRA = BMG('FRA', 'd', (500, 500), 'Fräsen')
QPR = BMG('QPR', 'e', (900, 300), 'Qualitätsprüfung')
FTL = BMG('FTL', 'f', (1300, 300), 'Fertigteillager', Lager=True)
LFF = BMG('LFF', 'g', (900, 100), 'Ladestation FFZ', Lager=True)

BMGen = [RTL, SAE, DRH, FRA, QPR, FTL, LFF]

def parse_datetime(datums_string:str):
    for format in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S"):
        try:

            return datetime.strptime(datums_string, format)
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

def PyGameDrawClock(screen, font, clockExtern, fps):
    text = f"{clockExtern.strftime("%d. %B %Y %H:%M")}"
    PyGameWrite(screen, font, text, (600, 600), 'top')
    # text = f"FPS: {round(fps,1)}"
    # PyGameWrite(screen, font, text, (1100, 700), 'left')

def PyGameSampleCurrentMovements(TLF, time, cars, currMovements):
    for mov in currMovements:
        if mov['EZP'] < time:
            currMovements.remove(mov)
            WaitingEZP = next((line['SZP'] for line in TLF if mov['FFZ_ID'] == line['FFZ_ID']), None)
            if WaitingEZP > mov['EZP']:
                currMovements.append({'VNR':'x', 'FFZ_ID':mov['FFZ_ID'],
                            'SK': mov['EK'], 'EK': mov['EK'],
                            # 'PyRoute': (mov['SK'], mov['EK']), 
                            'SZP': mov['EZP'],
                            'EZP': WaitingEZP})
    i = 0 # counter of movements, limited to number of cars
    for line in TLF:
        if i > len(cars):
            raise NotImplementedError(f'{i} orders for {len(cars)} cars')
        if line['SZP'] <= time and line['EZP'] > time: # Start liegt in der Vergangenheit, Ende aber in der Zukunft -> aktuell
            i += 1
            line['PyRoute'] = None
            currMovements.append(line)
            TLF.remove(line)
        if line['SZP'] > time:
            break 
        
    return currMovements

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


def PyGameDrawCars(screen, font, currMovements, time):
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

def format_dict(data, fmt="%H:%M"):
    if isinstance(data, dict):
        return {k: format_dict(v, fmt) for k, v in data.items()}
    elif isinstance(data, list):
        return [format_dict(item, fmt) for item in data]
    elif isinstance(data, tuple):
        return [format_dict(item, fmt) for item in data]
    elif isinstance(data, datetime):
        return data.strftime(fmt)
    elif isinstance(data, float):
        return round(data, 1)
    else:
        return data
        

def initPygame(stations:list[dict], cars:set, lines:list[dict], TLF:list[dict]) -> None:
    pygame.init()
    screen = pygame.display.set_mode((1400, 800))
    clock = pygame.time.Clock()
    framerate = 60 # fps
    SimSpeed = 1 # in seconds per minute
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
                    SimSpeed += 0.5
                    if SimSpeed > 10: SimSpeed = 10
                if event.key == pygame.K_DOWN:
                    SimSpeed -= 0.5
                    if SimSpeed < 0.5: SimSpeed = 0.5


        screen.fill((255, 255, 255))

        for bmg in BMGen:
            bmg.draw(screen, font)

        if states[state] == 'pause':
            Time = Time
        elif states[state] == 'unpause':
            passedTime = pygame.time.get_ticks() - passedTime
            Time += timedelta(milliseconds=passedTime) #* 0.5 * SimSpeed 
# TIME ?!?!?!

        fps = clock.get_fps()
        PyGameDrawClock(screen, font, Time, fps)

        currMovements = PyGameSampleCurrentMovements(TLF, Time, cars, currMovements)

        PyGameWrite(screen, font, f'Simspeed: {SimSpeed}, ticks: {pygame.time.get_ticks()}', (10, 500), 'left')

        i = 0
        for key in ['VNR', 'FFZ_ID', 'SK', 'EK', 'Startzeitpunkt', 'Endzeitpunkt']:
            PyGameWrite(screen, font, key, (10 + i * 50, 650), 'left')
            i += 1

        for j, mov in enumerate(currMovements):
            i = 0
            for key, value in mov.items():
                if key in ['VNR', 'FFZ_ID', 'SK', 'EK', 'SZP', 'EZP']:
                    if key in ['SZP', 'EZP']:
                        value.strftime('%H:%M')
                    PyGameWrite(screen, font, str(value), (10 + i * 50, 670 + j * 20), 'left')   
                    i += 1     

        # for i, mov in enumerate(currMovements):
        #     # offset = int(mov['FFZ_ID'][-1]) * 20
        #     if mov[i] in ['FFZ_ID', 'SK', 'EK', 'SZP', 'EZP']:
        #         print('yay')
        #     if mov['VNR'] != 'x':
        #         text = f"{mov['FFZ_ID']}   {mov['SK']}  ->  {mov['EK']})"
        #     else: text = f"{mov['FFZ_ID']}   waiting at {mov['SK']}"
        #     # PyGameWrite(screen, font, text, (50, 700 + offset), 'left')
        #     # formatedDict = format_dict(mov)
        #     # text = f"{formatedDict}"
        #     PyGameWrite(screen, font, text, (10, 650 + i * 20), 'left')

        PyGameDrawCars(screen, font, currMovements, Time)
        
        pygame.display.flip()
        clock.tick(framerate)



con = sqlite3.connect('prod_data.db')
cur = con.cursor()

TLF = getTLF(cur)
FFZ = {row['FFZ_ID'] for row in TLF} # set of used FFZ


B=1



initPygame(BMGen, FFZ, Lines, TLF)


a = 3

b= 1


con.close()
