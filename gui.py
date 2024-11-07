import sqlite3
import pygame
import sys

con = sqlite3.connect('prod_data.db')
cur = con.cursor()


def printDB():
    # FLF ----------------------------
    cur.execute("SELECT * FROM FLF")
    FLF = cur.fetchall()

    print(f"Inhalt der Tabelle: FLF (Fertigungs Log Files)")

    # Spaltennamen der Tabelle anzeigen
    FLFColumnNames = [description[0] for description in cur.description]
    print(", ".join(FLFColumnNames))  

    for row in FLF:
        formatiertes_tupel = [f"{wert:.2f}" if isinstance(wert, float) else str(wert) for wert in row]
        print("\t".join(formatiertes_tupel))

    # TLF ----------------------------
    cur.execute("SELECT * FROM TLF")
    TLF = cur.fetchall()

    print(f"Inhalt der Tabelle: TLF (Transport Log Files)")

    TLFColumnNames = [description[0] for description in cur.description]
    print(", ".join(TLFColumnNames)) 

    for row in TLF:
        formatiertes_tupel = [f"{wert:.2f}" if isinstance(wert, float) else str(wert) for wert in row]
        print("\t".join(formatiertes_tupel))

def getFLF():
    cur.execute("SELECT * FROM FLF")
    FLF = cur.fetchall()
    return FLF

def getTLF():
    # Vorgangsnummer, FFZ ID, Startknoten, Endknoten, Startzeitpunkt, Endzeitpunkt, Akkustand, Charge
    cur.execute("SELECT * FROM TLF")
    raw = cur.fetchall()
    keys = ['VorgangsNr', 'FFZ_ID', 'Startknoten', 'Endknoten', 'Startzeitpunkt', 'Endzeitpunkt', 'Akkustand', 'Charge']
    TLF = [dict(zip(keys, tupel)) for tupel in raw]
    return TLF

def PygameDrawStation(screen:pygame.surface.Surface, station:dict, font:pygame.font.Font) -> pygame.rect.Rect:
    main = (
        station['Pos'][0] - 0.5 * station['Size'][0], # left
        station['Pos'][1] - 0.5 * station['Size'][1], # top
        station['Size'][0], # width
        station['Size'][1] # height
    )
    pre = (
        main[0] - 1.2 * main[2], # left
        main[1] + 0.1 * main[3], # top
        1.2 * main[2], # width
        0.8 * main[3] # height
    )
    post = (
        main[0] + main[2], # left
        pre[1], # top
        pre[2], # width
        pre[3] # height
    )
    wrapper = (
        pre[0] - 10,
        main[1] - 50,
        pre[2] + main[2] + post[2] + 20,
        main[3] + 70,
    )
    label_text = f"{station['LongName']} ({station['Abbr']})"
    label = font.render(label_text, True, (0,0,0))
    label_rect = label.get_rect(center=(station['Pos'][0], main[1] - 0.5 * main[3]))
    screen.blit(label, label_rect)

    if station['ShortName'] not in ['RTL', 'LFF','FTL']: # lager haben keine pre und post lager
        Rect = pygame.draw.rect(screen, (0, 0, 0), wrapper, width=1, border_radius=10)            
        pygame.draw.rect(screen, (0, 0, 0), main, width=1, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), main, width=1, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), pre, width=1, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), post, width=1, border_radius=5)
    else:
        Rect = pygame.draw.rect(screen, (0, 0, 0), wrapper, width=1, border_radius=10)
    return Rect

def PygameDrawCar(screen:pygame.surface.Surface, car:str, stationRects:list, Offset:int, font:pygame.font.Font) -> pygame.rect.Rect:
    chargingStation = [item for item in stationRects if item.get('ShortName') == "LFF"]
    main = (
        chargingStation[0]['Rect'].midleft[0] + 10 + Offset, 
        chargingStation[0]['Rect'].midleft[1],
        20, 20
    )
    Rect = pygame.draw.rect(screen, (100,100,100), main, border_radius=3)
    label_text = f"{car}"
    label = font.render(label_text, True, (0,0,0))
    label_rect = label.get_rect(midbottom=(Rect.midtop))
    screen.blit(label, label_rect)
    
    return Rect

def PygameDrawLine(screen:pygame.surface.Surface,  stationRects:list) -> pygame.rect.Rect:
    pass

def CarMovement(screen, currMovement:list, lines:list, currTime:float):
    for movement in currMovement:
        for line in lines:
            if movement['Startknoten'] in [line['Start'], line['End']] and movement['Endknoten'] in [line['Start'], line['End']]:
                DistanceX = line['EndPoint'][0] - line['StartPoint'][0]
                DistanceY = line['EndPoint'][1] - line['StartPoint'][1]
                TimeRatio = (currTime - movement['Endzeitpunkt']) / (movement['Endzeitpunkt'] - movement['Startzeitpunkt'])
                NewPosition = (line['StartPoint'][0] + DistanceX * TimeRatio, line['StartPoint'][1] + DistanceY * TimeRatio, 190, 190)
                # for car in CarRects:
                #     if car.get('FFZ_ID') == movement['FFZ_ID']:
                #         car['Rect'].move(NewPosition)
                Rect = pygame.draw.rect(screen, (100,100,100), NewPosition, border_radius=3)
                a= 1
                        

def initPygame(stations:list, cars:set, lines:list, TLF:list) -> None:
    pygame.init()
    screen = pygame.display.set_mode((1400, 800))
    clock = pygame.time.Clock()
    framerate = 5 # 30 fps
    font = pygame.font.SysFont(None, 20)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.fill((255, 255, 255))

        StationRects = []
        for station in stations:
            Rect = PygameDrawStation(screen, station, font)
            StationRects.append({'ShortName': station['ShortName'], 'Rect': Rect})

        # CarRects = []
        # for i, car in enumerate(cars):
        #     Rect = PygameDrawCar(screen, car, StationRects, i * 25, font) # i is offset to avoid stacking
        #     CarRects.append({'FFZ_ID': car, 'Rect': Rect})

        currTime = pygame.time.get_ticks() / 1000

        for line in TLF:
            if line['Endzeitpunkt'] > currTime:
                break
            else:
                TLF.remove(line)

        currMovement = []
        i = 0 # counter of movements, limited to number of cars
        for line in TLF:
            if line['Startzeitpunkt'] < currTime:
                i += 1
                currMovement.append(line)
            if i >= len(cars):
                break

        CarMovement(screen, currMovement, lines, currTime)

        # TransportLines = []
        # for line in lines:
        #     Line = PygameDrawLine(screen, StationRects)
    
        pygame.display.flip()
        clock.tick(framerate)

BMGen = [   {'ShortName': 'RTL','Pos': (100, 300), 'Size': (50, 50), 'Abbr': 'a', 'LongName': 'Rohteillager'},
            {'ShortName': 'DRH','Pos': (500, 100), 'Size': (50, 50), 'Abbr': 'c', 'LongName': 'Drehen'},
            {'ShortName': 'SAE','Pos': (500, 300), 'Size': (50, 50), 'Abbr': 'b', 'LongName': 'Sägen'},
            {'ShortName': 'FRA','Pos': (500, 500), 'Size': (50, 50), 'Abbr': 'd', 'LongName': 'Fräsen'},
            {'ShortName': 'LFF','Pos': (900, 100), 'Size': (50, 50), 'Abbr': 'g', 'LongName': 'Ladestation FFZ'},
            {'ShortName': 'QPR','Pos': (900, 300), 'Size': (50, 50), 'Abbr': 'e', 'LongName': 'Qualitätsprüfung'},
            {'ShortName': 'FTL','Pos': (1300, 300), 'Size': (50, 50), 'Abbr': 'f', 'LongName': 'Fertigteillager'}
]

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

TLF = getTLF()
FFZ = {row['FFZ_ID'] for row in TLF} # set of used FFZ


B=1



initPygame(BMGen, FFZ, Lines, TLF)


a = 3

b= 1


con.close()
