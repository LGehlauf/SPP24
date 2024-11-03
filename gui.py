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

def initPygameDrawBMGen():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    stations = [(100, 100), (700, 100), (100, 500), (700, 500)]
    obj_pos = [100, 100]
    target_station = 1

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()



        screen.fill((255, 255, 255))

        for station in stations:
            pygame.draw.rect(screen, (0, 0, 0), station, 20)


    
        pygame.display.flip()
        clock.tick(30)



FLF = getFLF()

initPygameDrawBMGen()



b= 1

con.close()
