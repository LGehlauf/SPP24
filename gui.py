import sqlite3
import pygame
import sys
from datetime import datetime, timedelta
import re
import math


# to do: auslastung der fahrzeuge, anteil an leerfahrten (zb pro Schicht), zurückgelegter Weg

Lines = [   {'StartEnd': ['a', 'c'], 'Start': 'a', 'End': 'c', 'Distance': 15, 'StartPoint': (100, 220), 'EndPoint': (400, 145)},
            {'StartEnd': ['a', 'b'], 'Start': 'a', 'End': 'b', 'Distance': 11, 'StartPoint': (200, 285), 'EndPoint': (400, 285)},
            {'StartEnd': ['a', 'd'], 'Start': 'a', 'End': 'd', 'Distance': 16, 'StartPoint': (100, 350), 'EndPoint': (400, 485)},
            {'StartEnd': ['c', 'g'], 'Start': 'c', 'End': 'g', 'Distance': 12, 'StartPoint': (600, 85), 'EndPoint': (800, 85)},
            {'StartEnd': ['c', 'b'], 'Start': 'c', 'End': 'b', 'Distance': 6, 'StartPoint': (500, 150), 'EndPoint': (500, 220)},
            {'StartEnd': ['b', 'd'], 'Start': 'b', 'End': 'd', 'Distance': 5, 'StartPoint': (500, 350), 'EndPoint': (500, 420)},
            {'StartEnd': ['d', 'e'], 'Start': 'd', 'End': 'e', 'Distance': 17, 'StartPoint': (600, 485), 'EndPoint': (900, 350)},
            {'StartEnd': ['g', 'e'], 'Start': 'g', 'End': 'e', 'Distance': 6, 'StartPoint': (900, 150), 'EndPoint': (900, 220)},
            {'StartEnd': ['e', 'f'], 'Start': 'e', 'End': 'f', 'Distance': 14, 'StartPoint': (1000, 285), 'EndPoint': (1200, 285)},
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
        self.wrapper = (self.pre[0] - 10, self.main[1] - 50, self.pre[2] + self.main[2] + self.post[2] + 20, self.main[3] + 70)
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
    keys = ['VorgangsNr', 'FFZ_ID', 'Startknoten', 'Endknoten', 'Route', 'Startzeitpunkt', 'Endzeitpunkt', 'Akkustand', 'Charge']    
    TLF = []
    for tupel in raw:
        Dict = dict(zip(keys, tupel))
        Dict['Startzeitpunkt'] = parse_datetime(Dict['Startzeitpunkt'])
        Dict['Endzeitpunkt'] = parse_datetime(Dict['Endzeitpunkt'])
        Dict['Route'] = parse_route(Dict['Route'])
        TLF.append(Dict)
    return TLF


def PyGameDrawClock(screen, font, clockIntern, clockExtern, fps):
    # label_text = f"intern clock (seconds): {clockIntern}"
    # label = font.render(label_text, True, (0,0,0))
    # label_rect = label.get_rect(midright=(650, 700))
    # screen.blit(label, label_rect)
    label_text = f"{clockExtern.strftime("%d. %B %Y %H:%M")}"
    label = font.render(label_text, True, (0,0,0))
    label_rect = label.get_rect(midleft=(650, 700))
    screen.blit(label, label_rect)
    label_text = f"FPS: {round(fps,1)}"
    label = font.render(label_text, True, (0,0,0))
    label_rect = label.get_rect(midleft=(1100, 700))
    screen.blit(label, label_rect)

def CarMovement(screen, currMovement:list, lines:list, currTime, font):
    width, height = 10, 10
    for movement in currMovement:
        for line in lines:
            if movement['Startknoten'] in [line['Start'], line['End']] and movement['Endknoten'] in [line['Start'], line['End']]:
                # ich brauche hier die Koordinaten vom Startknoten
                DistanceX = line['EndPoint'][0] - line['StartPoint'][0]
                DistanceY = line['EndPoint'][1] - line['StartPoint'][1]
                try:
                    TimeRatio = (currTime - movement['Endzeitpunkt']) / (movement['Endzeitpunkt'] - movement['Startzeitpunkt'])
                except:
                    TimeRatio = 1
                    print("TimeRatio div by 0", movement, line)
                NewPosition = (line['StartPoint'][0] + DistanceX * TimeRatio, line['StartPoint'][1] + DistanceY * TimeRatio) #line['StartPoint'][0] falsch 
                rect = (NewPosition[0] - width * 0.5, NewPosition[1] - height * 0.5, width, height)  
                Rect = pygame.draw.rect(screen, (100,100,100), rect, border_radius=3)
                # a= 1
                try:
                    label_text = f"{movement['FFZ_ID']} {movement['Startknoten']}->{movement['Endknoten']})"
                    label = font.render(label_text, True, (0,0,0))
                    label_rect = label.get_rect(midbottom=Rect.midtop)
                    screen.blit(label, label_rect)
                except:
                    pass

def PyGameSampleCurrentMovements(TLF, time, cars, currMovements):
    for movement in currMovements:
        if movement['Endzeitpunkt'] < time:
            currMovements.remove(movement)
    i = 0 # counter of movements, limited to number of cars
    for line in TLF:
        if i > len(cars):
            raise NotImplementedError(f'{i} orders for {len(cars)} cars')
        if line['Startzeitpunkt'] <= time and line['Endzeitpunkt'] > time: # Start liegt in der Vergangenheit, Ende aber in der Zukunft -> aktuell
            i += 1
            line['PyRoute'] = None
            currMovements.append(line)
            TLF.remove(line)
        if line['Startzeitpunkt'] > time:
            break 
        
    return currMovements

def calcDistanceRatio(Route):
    cumuDistances = []
    cumuDistances.append(0)
    Sum = 0
    # get the distances given in Lines 
    for i in range(len(Route) - 1):
        for line in Lines:
            if Route[i] in line['StartEnd'] and Route[i+1] in line['StartEnd']:
                cumuDistances.append(line['Distance'] + cumuDistances[-1])
                Sum += line['Distance']
                break
    # cumuDistances.pop(0)
    return tuple(distance / Sum for distance in cumuDistances)

    
def PyGameDrawCars(screen, font, currMovements, time):
    width, height = 10, 10
    for mov in currMovements:
        if mov['PyRoute'] == None: # only executed once per movement
            mov['PyRoute'] = PyGameFindConnections(mov) # jetzt sind die zu fahrenden koordinaten bekannt
            mov['DistanceRatio'] = calcDistanceRatio(mov['Route']) # 
            mov['TravelTime'] = mov['Endzeitpunkt'] - mov['Startzeitpunkt']
            checkpointTimes = []
            for ratio in mov['DistanceRatio']:
                checkpointTimes.append(mov['Startzeitpunkt'] + ratio * mov['TravelTime'])    
            mov['CheckpointTimes'] = checkpointTimes
        
        
        for i in range(len(mov['PyRoute']) - 1):
            # welche strecke muss genau jetzt animiert werden? Dafür gibt es die CheckpointTimes
            if time > mov['CheckpointTimes'][i] and time < mov['CheckpointTimes'][i+1]:
                DistanceX = mov['PyRoute'][i][1][0] - mov['PyRoute'][i][0][0]
                DistanceY = mov['PyRoute'][i][1][1] - mov['PyRoute'][i][0][1]
                TimeRatio = (time - mov['CheckpointTimes'][i]) / (mov['CheckpointTimes'][i+1] - mov['CheckpointTimes'][i])
                PosX = mov['PyRoute'][i][0][0] + TimeRatio * DistanceX
                PosY = mov['PyRoute'][i][0][1] + TimeRatio * DistanceY
                rect = (PosX - width * 0.5, PosY - height * 0.5, width, height)  
                Rect = pygame.draw.rect(screen, (100,100,100), rect, border_radius=2)
                scaling_factor = int(mov['FFZ_ID'][-1]) * 20 
                label_text = f"trying {mov['FFZ_ID']}   {mov['Route'][i]}  ->  {mov['Route'][i+1]})"
                label = font.render(label_text, True, (0,0,0))
                label_rect = label.get_rect(midleft=(200, 700 + scaling_factor))
                screen.blit(label, label_rect)
                try:
                    label_text = f"{mov['FFZ_ID']} {mov['Startknoten']}->{mov['Endknoten']})"
                    label = font.render(label_text, True, (0,0,0))
                    label_rect = label.get_rect(midbottom=Rect.midtop)
                    screen.blit(label, label_rect)
                except:
                    pass
            


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
        

def initPygame(stations:list[dict], cars:set, lines:list[dict], TLF:list[dict]) -> None:
    pygame.init()
    screen = pygame.display.set_mode((1400, 800))
    clock = pygame.time.Clock()
    framerate = 60 # fps
    SimSpeed = 2 # in seconds per minute
    font = pygame.font.SysFont(None, 20)
    ExternStartTime = TLF[0]['Startzeitpunkt'] - timedelta(minutes=1)
    currMovements = []

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((255, 255, 255))

        for bmg in BMGen:
            bmg.draw(screen, font)

        currTimeIntern = pygame.time.get_ticks() / 1000
        currTimeExtern = ExternStartTime + timedelta(milliseconds=pygame.time.get_ticks()) * SimSpeed * 60
        fps = clock.get_fps()

        PyGameDrawClock(screen, font, currTimeIntern, currTimeExtern, fps)

        currMovements = PyGameSampleCurrentMovements(TLF, currTimeExtern, cars, currMovements)

        for mov in currMovements:
            scaling_factor = int(mov['FFZ_ID'][-1]) * 20 
            label_text = f"{mov['FFZ_ID']}   {mov['Startknoten']}  ->  {mov['Endknoten']})"
            label = font.render(label_text, True, (0,0,0))
            label_rect = label.get_rect(midleft=(50, 700 + scaling_factor))
            screen.blit(label, label_rect)

        PyGameDrawCars(screen, font, currMovements, currTimeExtern)
        
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
