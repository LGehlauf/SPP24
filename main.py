import simpy
import numpy as np



class Maschine:
    def __init__(self, env, maschinentyp,kapazitaet):
        self.env = env
        self.maschinentyp = maschinentyp
        self.maschinenkapa = simpy.Resource(env,kapazitaet) #Kapazität als begrenzte Ressource definiert


    def Bearbeitung(self, bauteil):
        if self.maschinentyp == 'Drehmaschine':
            self.env.process(Drehen(self.env, bauteil,self.maschinenkapa)) #Drehprozess gestartet, dafür wird ein bauteil benötigt
                                                        #hier kommt die resource als kapazität rein

class Bauteil:
    def __init__(self, env, teiletyp, zeit, anzahl):
        self.env = env
        self.teiletyp = teiletyp
        self.zeit = zeit
        self.anzahl = anzahl
        self.zaehler = 0
        self.bauteilcontainer= simpy.Container(env, anzahl, init=anzahl)


    def Drehteil(self):
        if self.teiletyp == 'Drehteil':
            self.zeit = np.loadtxt('Daten.csv',delimiter=';') #import von den daten aus der csv
            print(self.zeit) # zum debuggen. zeigt den datenvektor an

    #BauteilZähler: Damit nicht jede Maschine mit Teil 1 neu beginnt
    def Bauteilzaehler(self):
        if self.zaehler < self.anzahl:
            self.zaehler += 1
            print('Teile hergestellt:', self.zaehler)
            print('Noch zu produzieren:', self.anzahl - self.zaehler)




    # Getter-Methode
    def get_drehteil(self): #getter für drehteil bearbeitungszeit
        return self.zeit


# Bearbeitungsprozesse
def Drehen(env, bauteil,maschinenkapa):
    while bauteil.zaehler < bauteil.anzahl:
        #for bauteil.zaehler in range(bauteil.anzahl): #hier werden nacheinander alle bauteile bearbeitet. to-do: unterschiedliche zeiten, auf welche maschine kommt dann welches teil?
            print('Starte Bearbeitung von Teil', bauteil.zaehler+1)

            #Maschine anfordern
            with maschinenkapa.request() as request:
                yield request  # Warten, bis die Maschine verfügbar ist

                print("teil auf maschine gelegt; t[s]" + str(env.now))

                #bauteil anfordern
                yield bauteil.bauteilcontainer.get(1)

                print("Bauteil angefordert" + str(env.now))

                print("Auftrags- und Arbeitsmittelbereitstellung; t[s]=" + str(env.now))
                yield env.timeout(bauteil.get_drehteil()[0, 0])  # hier wird der erste eintrag des datenvektors genutzt
                print("CNC-Programm einlesen; t[s]=" + str(env.now))
                yield env.timeout(180)

                print("gibt das teil frei; t[s]" + str(env.now))

                # Einmal das bauteil zählen
                bauteil.Bauteilzaehler()

#problem: nach meiner bisherigen logik, gilt die anzahl jedes mal für die maschine, wenn bauteil 1 geladen wird

# Simulationsumgebung erstellen
env = simpy.Environment()

# Bauteil erstellen
bauteil1 = Bauteil(env, 'Drehteil', 10, 3)
bauteil1.Drehteil()  # Setzt die Bearbeitungszeit für das Drehteil



# Maschine erstellen
m1 = Maschine(env, 'Drehmaschine',1)
m1.Bearbeitung(bauteil1)  # Bauteil an Bearbeitung übergeben

#m2 = Maschine(env, 'Drehmaschine',1)
#m2.Bearbeitung(bauteil1)  # Bauteil an Bearbeitung übergeben


# Simulation starten
env.run(until=6000)
