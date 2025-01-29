# Dijkstra
from collections import namedtuple, deque

# Definiere ein namedtuple 'edge', um eine Kante zu repräsentieren, die einen Startknoten, Endknoten und die Kosten hat
edge = namedtuple('edge', 'start, end, cost')

# Hilfsfunktion, um eine Kante zu erstellen
def create_edge(start, end, cost):
    return edge(start, end, cost)

# Klasse für den Graphen
class graph:
    def __init__(self, edges):
        # Erstelle die Liste der Kanten für den Graphen
        self.edges = [create_edge(*e) for e in edges]

    # Methode, um alle Knoten (Vertices) des Graphen zu bekommen
    def vertices(self):
        # Nimm alle Start- und Endknoten der Kanten und füge sie zu einem Set zusammen, um doppelte Knoten zu vermeiden
        return set(
            e.start for e in self.edges
        ).union(e.end for e in self.edges)

    # Methode, um die Nachbarn eines Knotens (v) zu bekommen
    def get_neighbors(self, v):
        neighbors = []
        # Überprüfe jede Kante im Graphen
        for e in self.edges:
            # Wenn der Start der Kante der gegebene Knoten ist, füge den Endknoten und die Kosten als Nachbarn hinzu
            if e.start == v:
                neighbors.append((e.end, e.cost))
        return neighbors

    # Implementierung des Dijkstra-Algorithmus
    def dijkstra(self, source, destination):
        # Initialisiere ein Dictionary, das die minimalen Distanzen von der Quelle zu jedem Knoten speichert
        distances = {v: float("inf") for v in self.vertices()}
        # Initialisiere ein Dictionary, um den vorherigen Knoten zu speichern (für die Pfadrekonstruktion)
        prev_v = {v: None for v in self.vertices()}

        # Die Distanz zur Quelle ist 0
        distances[source] = 0
        # Erstelle eine Liste aller Knoten (Vertices)
        vertices = list(self.vertices())[:]

        # Solange es noch Knoten zu besuchen gibt
        while len(vertices) > 0:
            # Wähle den Knoten mit der kleinsten Distanz
            v = min(vertices, key=lambda u: distances[u])
            # Entferne diesen Knoten aus der Liste der zu besuchenden Knoten
            vertices.remove(v)

            # Wenn die minimale Distanz zu diesem Knoten "unendlich" ist, gibt es keine erreichbaren Knoten mehr
            if distances[v] == float("inf"):
                break

            # Gehe durch alle Nachbarn des aktuellen Knotens
            for neighbor, cost in self.get_neighbors(v):
                # Berechne die Kosten, um zum Nachbarn zu gelangen
                path_cost = distances[v] + cost
                # Wenn der neue Pfad kürzer ist, aktualisiere die Distanz und den Vorgänger des Nachbarn
                if path_cost < distances[neighbor]:
                    distances[neighbor] = path_cost
                    prev_v[neighbor] = v

        # Rekonstruiere den kürzesten Pfad, indem wir die Vorgänger verfolgen
        path = []
        curr_v = destination

        # Solange wir einen Vorgänger haben, fügen wir den aktuellen Knoten zum Pfad hinzu
        while prev_v[curr_v] is not None:
            path.insert(0, curr_v)  # Füge den Knoten vorne in die Liste ein
            curr_v = prev_v[curr_v]

        # Füge die Quelle zum Pfad hinzu
        path.insert(0, curr_v)

        # Die Gesamtdistanz des kürzesten Pfads
        total_distance = distances[destination]

        # Gib den kürzesten Pfad und seine Gesamtdistanz zurück
        return path, total_distance