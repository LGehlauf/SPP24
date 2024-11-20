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

Lines = [   {'StartEnd': ['a', 'c'], 'Distance': 70},
            {'StartEnd': ['a', 'b'], 'Distance': 60},
            {'StartEnd': ['a', 'd'], 'Distance': 75},
            {'StartEnd': ['c', 'g'], 'Distance': 40},
            {'StartEnd': ['c', 'b'], 'Distance': 25},
            {'StartEnd': ['b', 'd'], 'Distance': 45},
            {'StartEnd': ['d', 'e'], 'Distance': 85},
            {'StartEnd': ['g', 'e'], 'Distance': 30},
            {'StartEnd': ['e', 'f'], 'Distance': 85},
            {'StartEnd': ['g', 'h'], 'Distance': 45},
            {'StartEnd': ['e', 'h'], 'Distance': 55}
]

class Charge:
    def __init__(self, Charge_ID, ColID, Pos=(0,0), Radius=10, width=3):
        self.charge_ID = Charge_ID
        self.shortID = re.search(r'0+([1-9]\d*|0)$', self.charge_ID).group(1)
        self.colour = viridis_to_rgb(ColID)
        self.Pos = Pos
        self.radius = Radius
        self.width = width
        self.ChargeCirc = pygame.draw.circle(screen, self.colour, (0,0), radius=Radius, width=width)
    def drawSelf(self):
        PyGameWrite(f'{self.shortID}', self.Pos, 'center', size='small')
        pygame.draw.circle(screen, self.colour, self.Pos, self.radius, self.width)


class FFZ:
    def __init__(self, FFZ_ID, ColID, Akku, Size=(22,22)):
        self.FFZ_ID = FFZ_ID
        self.colour = viridis_to_rgb(ColID)
        self.Akku = Akku
        self.size = Size
        rect = (0, 0, *Size)
        self.CarRect = pygame.draw.rect(screen, self.colour, rect, border_radius=2)
    def drawSelf(self):
        # legend rect # position is of #BAUSTELLE
        PyGameWrite(f'{self.FFZ_ID}', (1000, int(self.FFZ_ID[-1])*20+700), 'left', size="normal")
        pygame.draw.rect(screen, self.colour, (1020, int(self.FFZ_ID[-1])*20+700, self.CarRect.width, self.CarRect.height), width=2,border_top_left_radius=2, border_top_right_radius=2)
        pygame.draw.rect(screen, (0,0,0), (1020, int(self.FFZ_ID[-1])*20+710,
                                        self.CarRect.width,
                                        5), width=1, border_bottom_left_radius=2, border_bottom_right_radius=2)
        pygame.draw.rect(screen, ampel_to_rgb(self.Akku),(1020, int(self.FFZ_ID[-1])*20+710,
                                        self.CarRect.width * self.Akku,
                                        5), border_bottom_left_radius=2, border_bottom_right_radius=2)
        # moving rect
        pygame.draw.rect(screen, self.colour, self.CarRect, width=2,border_top_left_radius=2, border_top_right_radius=2)
        pygame.draw.rect(screen, (0,0,0), (self.CarRect.bottomleft[0], 
                                        self.CarRect.bottomleft[1] + 2, 
                                        self.CarRect.width,
                                        5), width=1, border_bottom_left_radius=2, border_bottom_right_radius=2)
        pygame.draw.rect(screen, ampel_to_rgb(self.Akku),(self.CarRect.bottomleft[0], 
                                        self.CarRect.bottomleft[1] + 2, 
                                        self.CarRect.width * self.Akku,
                                        5), border_bottom_left_radius=2, border_bottom_right_radius=2)
        

class BMG:
    def __init__(self, ShortNames, Abbreviation, Pos, LongName, Size=(60,60), Lager=False):
        self.ShortNames = ShortNames
        self.Abbreviation = Abbreviation
        self.LongName = LongName
        self.Pos = Pos
        self.Size = (Size[0], Size[1] + Size[1] * 0.5 * (len(ShortNames)-1))
        self.Lager = Lager
        # left, top, width, height
        self.AnQ = []
        self.RZPQ = []
        self.BQ = []
        self.AbQ = []
        self.LagerQ = []
        self.mains = []
        for i in range(len(self.ShortNames)):
            self.mains.append((self.Pos[0] - 0.5 * self.Size[0], self.Pos[1] - 0.5 * self.Size[1] + i * (1 / len(self.ShortNames) * self.Size[1]), self.Size[0], 1 / len(self.ShortNames) * self.Size[1] ))
        self.pre = (self.mains[0][0] - 1.2 * self.mains[0][2], self.mains[0][1] + 4, 1.2 * self.mains[0][2], self.Size[1] - 8)
        self.post = (self.mains[0][0] + self.mains[0][2], self.pre[1], self.pre[2], self.pre[3])
            
        self.wrapper = (self.pre[0] - 10, self.mains[0][1] - 32, self.pre[2] + self.mains[0][2] + self.post[2] + 20, self.Size[1] + 80)
        self.label_text = f"{self.LongName} ({self.Abbreviation})"
        
    def drawSelf(self):
        label = font.render(self.label_text, True, (0,0,0))
        label_rect = label.get_rect(center=(self.Pos[0], self.wrapper[1]+ 15))
        screen.blit(label, label_rect)
        self.wrapperRect = pygame.draw.rect(screen, (0, 0, 0), self.wrapper, width=1, border_radius=10)
        self.Stations = (self.wrapperRect.midleft, self.wrapperRect.midtop, self.wrapperRect.midright, self.wrapperRect.midbottom)
        # for station in self.Stations:
        #     pygame.draw.circle(screen, (30,30,30), station, 5)
        if not self.Lager:
            self.preRect = pygame.draw.rect(screen, (0, 0, 0), self.pre, width=1, border_bottom_left_radius=4, border_top_left_radius=4)
            self.postRect = pygame.draw.rect(screen, (0, 0, 0), self.post, width=1, border_bottom_right_radius=4, border_top_right_radius=4)
            self.mainRects = []
            for main in self.mains:
                self.mainRects.append(pygame.draw.rect(screen, (0, 0, 0), main, width=1, border_radius=4))

    def drawQueues(self):
        # qText = f'Q: {self.EinQ}'
        # label = font.render(qText, True, (0,0,0))
        # label_rect = label.get_rect(center=(self.Pos[0], self.Pos[1]))
        # screen.blit(label, label_rect)
        if len(self.AnQ) > 0:
            xPos, yPos = self.preRect.topright[0] - 2 - self.AnQ[0].radius, self.preRect.topright[1] + 2 + self.AnQ[0].radius
        for i, ch in enumerate(self.AnQ):
            # yOff = xOff // 3
            # Pos = (self.preRect.topright[0] - self.preRect.width/6 - (self.preRect.width) / 3 * (xOff % 3), 
            #         self.preRect.topright[1] + self.preRect.height/4 + (self.preRect.height) / 2 * yOff)
            # ch.Pos = Pos
            if xPos - 2 - ch.radius < self.preRect.topleft[0]:
                xPos = self.preRect.topright[0] - 2 - ch.radius
                yPos += (2 + ch.radius) * 2
            ch.Pos = (xPos, yPos)
            ch.drawSelf()
            xPos -= (2 + ch.radius) * 2

        for tuple in self.RZPQ:
            if re.search(r'(\d+)', tuple[0]) != None:
                i = int(re.search(r'(\d+)', tuple[0]).group(0)) - 1
            else: i = 0
            charge = tuple[1]
            frac = tuple[2]
            BorRect = (self.mainRects[i].topleft[0]+2, self.mainRects[i].topleft[1] + self.mainRects[i].height * 0.2, frac * (self.mainRects[i].width-4), self.mainRects[i].height * 0.2)
            pygame.draw.rect(screen, (0,0,0), BorRect, border_radius=2, width = 1) 
            pygame.draw.circle(screen, charge.colour, (self.mainRects[i].centerx, self.mainRects[i].topleft[1] + self.mainRects[i].height * 0.7), 5)
        
        for tuple in self.BQ:
            if re.search(r'(\d+)', tuple[0]) != None:
                i = int(re.search(r'(\d+)', tuple[0]).group(0)) - 1
            else: i = 0
            charge = tuple[1]
            frac = tuple[2]
            colour = ampel_to_rgb(frac)
            BorRect = (self.mainRects[i].topleft[0]+2, self.mainRects[i].topleft[1] + self.mainRects[i].height * 0.2, (self.mainRects[i].width-4), self.mainRects[i].height * 0.2)
            ColRect = (self.mainRects[i].topleft[0]+2, self.mainRects[i].topleft[1] + self.mainRects[i].height * 0.2, frac * (self.mainRects[i].width-4), self.mainRects[i].height * 0.2)
            pygame.draw.rect(screen, (0,0,0), BorRect, border_radius=2, width = 1)
            pygame.draw.rect(screen, colour, ColRect, border_radius=2)
            pygame.draw.circle(screen, charge.colour, (self.mainRects[i].centerx, self.mainRects[i].topleft[1] + self.mainRects[i].height * 0.7), 5)

        for xOff, ch in enumerate(self.AbQ):
            yOff = xOff // 3
            Pos = (self.postRect.topleft[0] + self.postRect.width/6 + (self.postRect.width) / 3 * (xOff % 3), 
                    self.postRect.topleft[1] + self.postRect.height/4 + (self.postRect.height) / 2 * yOff)
            ch.Pos = Pos
            ch.drawSelf()

        for xOff, ch in enumerate(self.LagerQ):
            yOff = xOff // 15
            pygame.draw.circle(screen, ch.colour,
                               (self.wrapperRect.topright[0] - 12 - 12 * (xOff % 15), 
                                self.wrapperRect.topright[1] + 52 + 12 * yOff), radius=5)

BMGen = [
    BMG(['RTL'], 'a', (200, 300), 'Rohteillager', Lager=True),
    BMG(['SAE'], 'b', (550, 300), 'Sägen'),
    BMG(['DRH1', 'DRH2'], 'c', (550, 100), 'Drehen'),
    BMG(['FRA'], 'd', (550, 500), 'Fräsen'),
    BMG(['QPR'], 'e', (850, 300), 'Qualitätsprüfung'),
    BMG(['FTL'], 'f', (1200, 300), 'Fertigteillager', Lager=True),
    BMG(['LFF'], 'g', (850, 100), 'Ladestation FFZ', Lager=True, Size=(50,0)),
    BMG(['HAE'], 'h', (1200, 100), 'Härten')
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
    keys = ['VNR', 'FFZ_ID', 'SK', 'EK', 'Route', 'SZP', 'EZP', 'lAkku', 'Charge']
    TLF = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        Dict['SZP'] = parse_datetime(Dict['SZP'])
        Dict['EZP'] = parse_datetime(Dict['EZP'])
        Dict['Route'] = parse_route(Dict['Route'])
        TLF.append(Dict)

    splits = defaultdict(list)
    for line in TLF:
        line['PyRoute'] = None # important for calculation of Routes 
        splits[line['FFZ_ID']].append(line)

    for key in splits: # split ist nicht das element sondern der key
        for i in range(len(splits[key]) - 1):
            thisLine = splits[key][i]
            nextLine = splits[key][i+1]    
            thisLine['nAkku'] = nextLine['lAkku']
            
            # splits[key][i]['nextAkku'] = nextline
            # gibt es eine zeitliche Lücke zwischen Start- und Endzeitpunkt der Fahrten?
            if thisLine['EZP'] < nextLine['SZP']: 
                # print(f'{key} waits between {thisLine['VNR']} and {nextLine['VNR']} from {thisLine['EZP']} to {nextLine['SZP']}')
                splits[key].append({'VNR':'x', 'FFZ_ID':thisLine['FFZ_ID'],
                                'SK': thisLine['EK'], 'EK': thisLine['EK'],
                                'SZP': thisLine['EZP'], 'EZP': nextLine['SZP'],
                                'lAkku': thisLine['lAkku'], 'nAkku': nextLine['lAkku']})
            if thisLine['EZP'] > nextLine['SZP']: # negative Zeit!
                splits[key].append({'VNR':'negT', 'FFZ_ID':thisLine['FFZ_ID'],
                                'SK': thisLine['EK'], 'EK': nextLine['SK'],
                                'SZP': thisLine['EZP'], 'EZP': nextLine['SZP'],
                                'lAkku': thisLine['lAkku'], 'nAkku': nextLine['lAkku']})
            if thisLine['EK'] != nextLine['SK']: # teleport!!
                # raise AssertionError(f'{key} teleported between {thisLine['VNR']} and {nextLine['VNR']} from {thisLine['EK']} to {nextLine['SK']}')
                splits[key].append({'VNR':'t', 'FFZ_ID':thisLine['FFZ_ID'],
                                'SK': thisLine['EK'], 'EK': nextLine['SK'],
                                'SZP': thisLine['EZP'], 'EZP': nextLine['SZP'],
                                'lAkku': thisLine['lAkku'], 'nAkku': nextLine['lAkku']})
    combined_list = [item for sublist in splits.values() for item in sublist]
    sorted_list = sorted(combined_list, key=lambda x: x['SZP'])
    return sorted_list

def getFLF(cur):
    cur.execute("SELECT * FROM FLF")
    raw = cur.fetchall()
    #keys = ['Charge', 'BMG', 'Ankunft', 'Start_Ruesten', 'Start_Bearbeitung', 'Ende_Bearbeitung', 'Abtransport', 'Anzahl_Bauteile', 'Ausschuss']
    keys = ['Ch', 'BMG', 'AnZP', 'RZP', 'SB', 'EB', 'AbZP', 'Anz_Bauteile', 'Ausschuss'] 
    FLF = []
    for tupel in raw:
        lst = list(tupel)
        # if tupel[1] == "DRH1" or tupel[1] == "DRH2":
        #     lst[1] = "DRH"
        Dict = dict(zip(keys, lst))
        for key in ['AnZP', 'RZP', 'SB', 'EB', 'AbZP']:
            Dict[key] = parse_datetime(Dict[key])
        FLF.append(Dict)
    return FLF
    

def PyGameDrawClock(clockExtern, fps):
    text = f"{clockExtern.strftime("%d. %B %Y %H:%M")}"
    PyGameWrite(text, (20, 20), 'left')
    # text = f"FPS: {round(fps,1)}"
    # PyGameWrite(screen, text, (1100, 700), 'left')

def SampleCurrMovements(TLF, time):
    cM = [mov for mov in TLF if mov['SZP'] <= time and mov['EZP'] > time] 
    return cM

def SampleCurrChargen(FLF, time):
    cC = [
        Ch for Ch in FLF 
        if Ch['AnZP'] is not None and Ch['AnZP'] <= time and (
            Ch['AbZP'] is None or Ch['AbZP'] > time
        )
    ]
    return cC

def viridis_to_rgb(fraction):
    cmap = plt.get_cmap('viridis')
    rgb = cmap(fraction)[:3]
    rgb_255 = tuple(int(x * 255) for x in rgb)
    return rgb_255

def ampel_to_rgb(fraction):
    return (int((1 -fraction) * 255), int(fraction * 255), 0)

def PyGameDrawChargen(currChargen, time):
    for Ch in currChargen:
        ch = next((ch for ch in Chargen if ch.charge_ID == Ch['Ch']), None)
        bmg = next((bmg for bmg in BMGen if Ch['BMG'] in bmg.ShortNames ), None)
        if bmg == None:
            raise NotImplementedError(f'Charge {Ch} has no BMG')
        
        if bmg.Lager == True:
            bmg.LagerQ.append(ch)
        elif Ch['AnZP'] <= time and time < Ch['RZP']:
            bmg.AnQ.append(ch)
        elif Ch['RZP'] <= time and time < Ch['SB']:
            DurrRatio = (time-Ch['RZP']) / (Ch['SB'] - Ch['RZP'])
            bmg.RZPQ.append((Ch['BMG'], ch, DurrRatio))     
        elif Ch['SB'] <= time and time < Ch['EB']:   
            DurrRatio = (time - Ch['SB']) / (Ch['EB'] - Ch['SB'])
            bmg.BQ.append((Ch['BMG'], ch, DurrRatio))
        elif Ch['EB'] <= time and time < Ch['AbZP']:
            bmg.AbQ.append(ch)
            
    for bmg in BMGen:
        bmg.drawQueues()
        bmg.LagerQ = []
        bmg.AnQ = []
        bmg.RZPQ = []
        bmg.BQ = []
        bmg.AbQ = []   


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

def CalcPyRouteVariables(mov):
    mov['PyRoute'] = PyGameFindConnections(mov) # jetzt sind die zu fahrenden koordinaten bekannt
    mov['DistanceRatio'] = calcDistanceRatio(mov['Route']) # 
    mov['TravelTime'] = mov['EZP'] - mov['SZP']
    checkpointTimes = []
    for ratio in mov['DistanceRatio']:
        checkpointTimes.append(mov['SZP'] + ratio * mov['TravelTime'])    
    mov['CheckpointTimes'] = checkpointTimes
   
def PyGameDrawCars(currMovements, time):
    for mov in currMovements:
        ffz = next((ffz for ffz in FFZs if ffz.FFZ_ID == mov['FFZ_ID']), None)
        if mov['VNR'] != 'x':
            if mov['PyRoute'] == None: # only executed once per movement
                CalcPyRouteVariables(mov)
                
            for i in range(len(mov['Route']) - 1):
                # welche strecke muss genau jetzt animiert werden? Dafür gibt es die CheckpointTimes
                if time > mov['CheckpointTimes'][i] and time < mov['CheckpointTimes'][i+1]:
                    DistanceX = mov['PyRoute'][i][1][0] - mov['PyRoute'][i][0][0]
                    DistanceY = mov['PyRoute'][i][1][1] - mov['PyRoute'][i][0][1]
                    TimeRatio = (time - mov['CheckpointTimes'][i]) / (mov['CheckpointTimes'][i+1] - mov['CheckpointTimes'][i])
                    PosX = mov['PyRoute'][i][0][0] + TimeRatio * DistanceX
                    PosY = mov['PyRoute'][i][0][1] + TimeRatio * DistanceY
                    ffz.CarRect.center=(PosX, PosY)
                    if mov['Charge'] != None:
                        ch = next((ch for ch in Chargen if ch.charge_ID == mov['Charge']))
                        ch.Pos = ffz.CarRect.center
                        ch.drawSelf()
                    
        else: # current movement is waiting
            TimeRatio = (time - mov['SZP']) / (mov['EZP'] - mov['SZP'])
            offset = int(mov['FFZ_ID'][-1]) * 22
            WS = next((bmg for bmg in BMGen if bmg.Abbreviation == mov['SK']), None) # Waiting Station
            ffz.CarRect.center=(WS.wrapper[0] + 20 + offset, WS.wrapper[1] + WS.wrapper[3] - 20)
            
        Akku = mov['lAkku'] + (mov['nAkku'] - mov['lAkku']) * TimeRatio
        ffz.Akku = Akku
        ffz.drawSelf()
        # pygame.draw.rect(screen, ffz.colour, ffz.CarRect, width=2, border_top_left_radius=2, border_top_right_radius=2)
        # pygame.draw.rect(screen, (0,0,0), (ffz.CarRect.bottomleft[0], 
        #                                 ffz.CarRect.bottomleft[1] + 2, 
        #                                 ffz.CarRect.width,
        #                                 5), width=1, border_bottom_left_radius=2, border_bottom_right_radius=2)
        
        # pygame.draw.rect(screen, ampel_to_rgb(Akku),(ffz.CarRect.bottomleft[0], 
        #                                 ffz.CarRect.bottomleft[1] + 2, 
        #                                 ffz.CarRect.width * Akku,
        #                                 5), border_bottom_left_radius=2, border_bottom_right_radius=2)
                    
            
def PyGameWrite(text, Pos, LRTDC, size = 'normal'):
    if size == 'normal':
        label = font.render(text, True, (0,0,0))
    elif size == 'small':
        label = smallfont.render(text, True, (0,0,0))
    elif size == 'tiny':
        label = tinyfont.render(text, True, (0,0,0))
    if (LRTDC == 'left'): label_rect = label.get_rect(midleft=Pos)
    elif (LRTDC == 'right'): label_rect = label.get_rect(midright=Pos)
    elif (LRTDC == 'top'): label_rect = label.get_rect(midtop=Pos)
    elif (LRTDC == 'bottom'): label_rect = label.get_rect(midbottom=Pos)
    elif (LRTDC == 'center'): label_rect = label.get_rect(center=Pos)
    screen.blit(label, label_rect)

def initPygame():
    #FFZ = {row['FFZ_ID'] for row in TLF} # set of used FFZ
    pygame.init()
    global screen
    screen = pygame.display.set_mode((1400, 800))
    clock = pygame.time.Clock()
    framerate = 60 # fps
    dirPath = os.path.dirname(os.path.abspath(__file__)).replace('\\', '/')
    fontPath = dirPath + '/SourceSans3-Regular.ttf'
    global font
    font = pygame.font.Font(fontPath, 14)
    global smallfont
    smallfont =pygame.font.Font(fontPath, 10)
    global tinyfont
    tinyfont = pygame.font.Font(fontPath, 8)

    FFZ_set = {row['FFZ_ID'] for row in TLF} # set of used FFZ
    global FFZs
    FFZs = []
    for ffz in FFZ_set:
        ColID = (int(ffz[-1]) -1) / (len(FFZ_set)-1)
        FFZs.append(FFZ(ffz, ColID, 1))

    Charge_set = {row['Ch'] for row in FLF}
    global Chargen
    Chargen = []
    for i, Ch in enumerate(Charge_set):
        ColID = (i * 1.13) - int(i * 1.13)
        Chargen.append(Charge(Ch, ColID))
    a=0

    Time = TLF[0]['SZP'] - timedelta(minutes=1)
    passedTime = 0
    states = ['unpause', 'pause']
    state = 0
    SimSpeeds = [-128, -32, -8, -2, -1, -0.5, -0.25, 0.25, 0.5, 1, 2, 8, 32, 128]
    SimSpeed = 9
    mainloopPygame(clock, framerate, passedTime, Time, SimSpeeds, SimSpeed, states, state)


def mainloopPygame(clock, framerate, passedTime, Time, SimSpeeds, SimSpeed, states, state):
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
                if event.key == pygame.K_LEFT:
                    Time -= timedelta(hours=1)
                if event.key == pygame.K_RIGHT:
                    Time += timedelta(hours=1)
                # if event.key == pygame.K_LEFT and event.key == pygame.KMOD_LSHIFT:
                #     Time -= timedelta(hours=1)
                # if event.key == pygame.K_RIGHT and event.key == pygame.KMOD_LSHIFT:
                #     Time += timedelta(hours=1)
                # if event.key == pygame.K_LEFT and event.key == pygame.KMOD_LCTRL:
                #     Time -= timedelta(hours=2)
                # if event.key == pygame.K_RIGHT and event.key == pygame.KMOD_LCTRL:
                #     Time += timedelta(hours=2)
                

        screen.fill((255, 255, 255))

        for bmg in BMGen:
            bmg.drawSelf()

        if states[state] == 'pause':
            Time = Time
        elif states[state] == 'unpause':
            Time += timedelta(milliseconds=passedTime) * 60 * SimSpeeds[SimSpeed]
            passedTime = clock.get_time()

        fps = clock.get_fps()
        PyGameDrawClock(Time, fps)

        currMovements = SampleCurrMovements(TLF, Time)
        currChargen = SampleCurrChargen(FLF, Time)

        PyGameWrite(f'Simulation speed: {SimSpeeds[SimSpeed]}', (20, 40), 'left')

        i = 0
        for key in ['VNR', 'FFZ_ID', 'SK', 'EK', 'SZP', 'EZP', 'lAkku', 'nAkku']:
            PyGameWrite(key, (10 + i * 50, 650), 'left')
            i += 1

        for j, mov in enumerate(currMovements):
            i = 0
            for key, value in mov.items():
                if key in ['VNR', 'FFZ_ID', 'SK', 'EK', 'SZP', 'EZP', 'lAkku', 'nAkku']:
                    if key in ['lAkku', 'nAkku']:
                        value = round(value * 100)

                    if key in ['SZP', 'EZP']:
                        value = value.strftime('%H:%M')
                    PyGameWrite(str(value), (10 + i * 50, 670 + j * 20), 'left')
                    i += 1
        
        ChargenNoLager = [ch for ch in currChargen if ch['BMG'] not in ['RTL', 'FTL']]
        i = 0
        for key in ['Ch', 'BMG', 'AnZP', 'SB', 'EB', 'AbZP']:
            PyGameWrite(key, (500 + i * 50, 655), 'left')
            i += 1
        PyGameWrite("len(Ch): "+str(len(ChargenNoLager)), (800, 655), 'left')
        for j, mov in enumerate(ChargenNoLager):
            i = 0
            for key, value in mov.items():
                if key in ['Ch', 'BMG', 'AnZP', 'SB', 'EB', 'AbZP']:
                    if value != None and key in ['AnZP', 'SB', 'EB', 'AbZP']:
                        value = value.strftime('%H:%M')   
                    PyGameWrite(str(value), (500 + (i % 7)* 50, 670 + j * 15), 'left', 'small')
                    i += 1
        

        PyGameDrawCars(currMovements, Time)
        PyGameDrawChargen(currChargen, Time)
        
        pygame.display.flip()
        clock.tick(framerate)

con = sqlite3.connect('prod_data.db')
cur = con.cursor()

TLF = getTLF(cur)


FLF = getFLF(cur)


a =0


initPygame()

con.close()
