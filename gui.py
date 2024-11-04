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
    cur.execute("SELECT * FROM TLF")
    TLF = cur.fetchall()
    return TLF

def initPygameDrawBMGen(stations):
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()



        screen.fill((255, 255, 255))

        for station in stations:
            pygame.draw.circle(screen, (0, 0, 0), station['Pos'], 20)


    
        pygame.display.flip()
        clock.tick(30)

BMGen = [   {'ShortName': 'RTL','Pos': (100, 300), 'Size': (50, 50), 'LongName': 'Rohteillager'},
            {'ShortName': 'DRH','Pos': (300, 500), 'Size': (50, 50), 'LongName': 'Drehen'},
            {'ShortName': 'SAE','Pos': (300, 300), 'Size': (50, 50), 'LongName': 'Sägen'},
            {'ShortName': 'FRA','Pos': (300, 100), 'Size': (50, 50), 'LongName': 'Fräsen'},
            {'ShortName': 'LFF','Pos': (500, 500), 'Size': (50, 50), 'LongName': 'Ladestation Flurförderfahrzeuge'},
            {'ShortName': 'QPR','Pos': (500, 300), 'Size': (50, 50), 'LongName': 'Qualitätsprüfung'},
            {'ShortName': 'FTL','Pos': (700, 300), 'Size': (50, 50), 'LongName': 'Fertigteillager'}
        ]




initPygameDrawBMGen(BMGen)


FLF = getFLF()


b= 1


con.close()
