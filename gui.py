import sqlite3

# Verbindung zur bestehenden Datenbank herstellen
conn = sqlite3.connect('prod_data.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'FLF' OR name LIKE 'TLF';
''')
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    print(f"Inhalt der Tabelle: {table_name}")
    cursor.execute(f'SELECT * FROM {table_name}')
    rows = cursor.fetchall()
    

    # Spaltennamen der Tabelle anzeigen
    column_names = [description[0] for description in cursor.description]
    print("\t".join(column_names))  # Spaltennamen drucken
    
    for row in rows:
        formatiertes_tupel = [f"{wert:.2f}" if isinstance(wert, float) else str(wert) for wert in row]
        print("\t".join(formatiertes_tupel))

    # for row in formatierte_daten:
    #     print(row)
    print("\n" + "-"*50 + "\n")  # Trennlinie für bessere Lesbarkeit

conn.close()
# Verbindung schließen