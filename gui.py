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
    TLF = cur.fetchall()
    return TLF

def PygameDrawStation(screen, station, font):
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

def PygameDrawCar(screen, car, StationRects, Offset, font):
    chargingStation = [item for item in StationRects if item.get('ShortName') == "LFF"]
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
    
    return 

def initPygame(stations, cars):
    pygame.init()
    screen = pygame.display.set_mode((1400, 800))
    clock = pygame.time.Clock()
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

        CarRects = []
        for i, car in enumerate(cars):
            Rect = PygameDrawCar(screen, car, StationRects, i * 25, font)
            CarRects.append({'FFZ_ID': car, 'Rect': Rect})
    
        pygame.display.flip()
        clock.tick(30)

BMGen = [   {'ShortName': 'RTL','Pos': (100, 300), 'Size': (50, 50), 'Abbr': 'a', 'LongName': 'Rohteillager'},
            {'ShortName': 'DRH','Pos': (500, 100), 'Size': (50, 50), 'Abbr': 'c', 'LongName': 'Drehen'},
            {'ShortName': 'SAE','Pos': (500, 300), 'Size': (50, 50), 'Abbr': 'b', 'LongName': 'Sägen'},
            {'ShortName': 'FRA','Pos': (500, 500), 'Size': (50, 50), 'Abbr': 'd', 'LongName': 'Fräsen'},
            {'ShortName': 'LFF','Pos': (900, 100), 'Size': (50, 50), 'Abbr': 'g', 'LongName': 'Ladestation FFZ'},
            {'ShortName': 'QPR','Pos': (900, 300), 'Size': (50, 50), 'Abbr': 'e', 'LongName': 'Qualitätsprüfung'},
            {'ShortName': 'FTL','Pos': (1300, 300), 'Size': (50, 50), 'Abbr': 'f', 'LongName': 'Fertigteillager'}
        ]


TLF = getTLF()
FFZ = {row[1] for row in TLF} # set of used FFZ


B=1


initPygame(BMGen, FFZ)




b= 1


con.close()
