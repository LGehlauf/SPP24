import sqlite3
import pygame
import sys
from datetime import datetime, timedelta
import re


# to do: auslastung der fahrzeuge, anteil an leerfahrten (zb pro Schicht), zurückgelegter Weg

Lines = [   {'Start': 'a', 'End': 'c', 'Distance': 15, 'StartPoint': (100, 220), 'EndPoint': (400, 145)},
            {'Start': 'a', 'End': 'b', 'Distance': 11, 'StartPoint': (200, 285), 'EndPoint': (400, 285)},
            {'Start': 'a', 'End': 'd', 'Distance': 16, 'StartPoint': (100, 350), 'EndPoint': (400, 485)},
            {'Start': 'c', 'End': 'g', 'Distance': 12, 'StartPoint': (600, 85), 'EndPoint': (800, 85)},
            {'Start': 'c', 'End': 'b', 'Distance': 6, 'StartPoint': (500, 150), 'EndPoint': (500, 220)},
            {'Start': 'b', 'End': 'd', 'Distance': 5, 'StartPoint': (500, 350), 'EndPoint': (500, 420)},
            {'Start': 'd', 'End': 'e', 'Distance': 17, 'StartPoint': (600, 485), 'EndPoint': (900, 350)},
            {'Start': 'g', 'End': 'e', 'Distance': 6, 'StartPoint': (900, 150), 'EndPoint': (900, 220)},
            {'Start': 'e', 'End': 'f', 'Distance': 14, 'StartPoint': (1000, 285), 'EndPoint': (1200, 285)},
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

def PyGameSampleCurrentMovements(TLF, time, cars):
    currMovement = []
    for line in TLF:
        if line['Endzeitpunkt'] > time:
            break
        else:
            TLF.remove(line)
    i = 0 # counter of movements, limited to number of cars
    for line in TLF:
        if line['Startzeitpunkt'] <= time:
            i += 1
            currMovement.append(line)
        if i >= len(cars):
            break
    return currMovement

def PyGameDrawCars(screen, font, movement, time):
    PyGameFindConnection(movement['Route'])
    pass

def PyGameFindConnections(Route):
    for i in range(len(Route)):
        if i == len(Route) - 1:
            break
        Route[i]
                        

def initPygame(stations:list[dict], cars:set, lines:list[dict], TLF:list[dict]) -> None:
    pygame.init()
    screen = pygame.display.set_mode((1400, 800))
    clock = pygame.time.Clock()
    framerate = 60 # fps
    SimSpeed = 3 # in seconds per minute
    font = pygame.font.SysFont(None, 20)
    ExternStartTime = TLF[0]['Startzeitpunkt']

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((255, 255, 255))

        # StationRects = []
        # for station in stations:
        #     Rect = PygameDrawStation(screen, station, font)
        #     StationRects.append({'ShortName': station['ShortName'], 'Rect': Rect})
        for bmg in BMGen:
            bmg.draw(screen, font)

        currTimeIntern = pygame.time.get_ticks() / 1000
        currTimeExtern = ExternStartTime + timedelta(milliseconds=pygame.time.get_ticks()) * SimSpeed * 60
        fps = clock.get_fps()

        PyGameDrawClock(screen, font, currTimeIntern, currTimeExtern, fps)

        currMovement = PyGameSampleCurrentMovements(TLF, currTimeExtern, cars)

        PyGameDrawCars(screen, font, currMovement, currTimeExtern)
        
        # CarMovement(screen, currMovement, lines, currTimeExtern, font)

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
