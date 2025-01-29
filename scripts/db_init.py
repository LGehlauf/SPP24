def db_init():
    import sqlite3

    # neue Datenbank erstellen
    conn = sqlite3.connect('prod_data.db')
    cursor = conn.cursor()

    # Tabellen löschen, falls sie existieren
    cursor.execute('DROP TABLE IF EXISTS produktstammdaten')
    cursor.execute('DROP TABLE IF EXISTS auftraege')
    cursor.execute('DROP TABLE IF EXISTS betriebsmittel')
    cursor.execute('DROP TABLE IF EXISTS arbeitsplaene')
    cursor.execute('DROP TABLE IF EXISTS ffz')
    cursor.execute('DROP TABLE IF EXISTS FLF')
    cursor.execute('DROP TABLE IF EXISTS TLF')
    cursor.execute('DROP TABLE IF EXISTS ELF')

    # Produktstammdaten 
    cursor.execute('''create table if not exists produktstammdaten (
            id varchar primary key unique,  
            bezeichnung text,
            dlz_plan integer,
            losgroesse integer,
            Bestand_RTL integer,
            Bestand_FTL integer,
            Bestellbestand integer)''') # weitere Spalten sind zu definieren

    # Aufträge
    cursor.execute('''create table if not exists auftraege (
            Charge integer primary key autoincrement,
            id varchar,
            stueckzahl_plan integer,
            stueckzahl_ist interger,
            freigabe integer,
            fertigstellung integer,
            art text, 
            FOREIGN KEY (id) REFERENCES produktstammdaten(id))''') # weitere Spalten sind zu definieren

    # Betriebsmittel
    cursor.execute('''create table if not exists betriebsmittel (
            bmg varchar primary key,
            bezeichnung varchar,
            knoten varchar)''') # weitere Spalten sind zu definieren

    # Arbeitspläne
    cursor.execute('''create table if not exists arbeitsplaene (
            id varchar,
            nr varchar,
            bmg varchar,
            r_plan integer,
            t_plan integer,
            PRIMARY KEY (id, nr),
            FOREIGN KEY (id) REFERENCES produktstammdaten(id))''') # weitere Spalten sind zu definieren

    # Flurförderzeuge
    cursor.execute('''create table if not exists ffz (
            id varchar primary key unique,
            speed integer,
            akkukapazitaet integer)''') # weitere Spalten sind zu definieren

    # Fertigungs-Log-Files = FLF
    cursor.execute('''create table if not exists FLF (
            Charge varchar,
            bmg varchar,
            ankunft integer,
            start_ruesten integer,
            start_bearbeitung integer,
            ende_bearbeitung integer,
            abtransport integer,
            anzahl_bauteile interger,
            ausschuss integer,
            primary key (Charge, bmg),
            FOREIGN KEY (bmg) REFERENCES betriebsmittel(bmg),
            FOREIGN KEY (charge) REFERENCES auftraege(charge))''') # weitere Spalten sind zu definieren

    # Transport-Log-Files = TLF
    cursor.execute('''create table if not exists TLF (
            Vorgangs_nr integer primary key autoincrement,
            FFZ_id varchar,
            start_knoten varchar,
            end_knoten varchar,
            route text,
            startzeitpunkt integer,
            endzeitpunkt integer, 
            akkustand integer,       
            charge varchar,
            FOREIGN KEY (charge) REFERENCES auftraege(charge))''') # weitere Spalten sind zu definieren

    # Error-Log-Files = ELF
    cursor.execute('''create table if not exists ELF (
            Vorgangs_nr integer primary key autoincrement,
            bmg varchar,
            start_downtime integer,
            end_downtime integer,
            reststandzeit integer,
            type text,
            FOREIGN KEY (bmg) REFERENCES betriebsmittel(bmg))''') # weitere Spalten sind zu definieren

    # Setze den Startwert von Charge auf 20000000
    cursor.execute('INSERT INTO sqlite_sequence (name, seq) VALUES ("auftraege", 19999999)')
    # Setze den Startwert von Charge auf 1
    cursor.execute('INSERT INTO sqlite_sequence (name, seq) VALUES ("TLF", 0)')
    # Setze den Startwert von Charge auf 1
    cursor.execute('INSERT INTO sqlite_sequence (name, seq) VALUES ("ELF", 0)')

    # Stammdaten pflegen
    cursor.execute('INSERT INTO produktstammdaten (id, bezeichnung, dlz_plan, losgroesse, bestand_rtl, bestand_ftl, bestellbestand) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                ('A1', 'Gehause', '50', '25', '700', '140', '150'))
    cursor.execute('INSERT INTO produktstammdaten (id, bezeichnung, dlz_plan, losgroesse, bestand_rtl, bestand_ftl, bestellbestand) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                ('A2', 'Deckel', '150', '50', '400', '170', '250'))
    cursor.execute('INSERT INTO produktstammdaten (id, bezeichnung, dlz_plan, losgroesse, bestand_rtl, bestand_ftl, bestellbestand) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                ('A3', 'Zylinderrohr', '200', '50', '330', '310', '250'))
    cursor.execute('INSERT INTO produktstammdaten (id, bezeichnung, dlz_plan, losgroesse, bestand_rtl, bestand_ftl, bestellbestand) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                ('A4', 'Zylinderboden', '200', '100', '530', '70', '300'))
    cursor.execute('INSERT INTO produktstammdaten (id, bezeichnung, dlz_plan, losgroesse, bestand_rtl, bestand_ftl, bestellbestand) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                ('A5', 'Kolbenstange', '200', '50', '530', '230', '190'))
    cursor.execute('INSERT INTO produktstammdaten (id, bezeichnung, dlz_plan, losgroesse, bestand_rtl, bestand_ftl, bestellbestand) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                ('A6', 'Zahnrad', '200', '100', '530', '230', '500'))
    cursor.execute('INSERT INTO produktstammdaten (id, bezeichnung, dlz_plan, losgroesse, bestand_rtl, bestand_ftl, bestellbestand) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                ('A7', 'Welle', '200', '25', '530', '190', '150'))
    cursor.execute('INSERT INTO produktstammdaten (id, bezeichnung, dlz_plan, losgroesse, bestand_rtl, bestand_ftl, bestellbestand) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                ('A8', 'Kolben', '200', '100', '330', '310', '250'))

    # Arbeitspläne
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A1', '20', 'FRA', '15', '10'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A1', '30', 'QPR', '15', '3'))

    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)',
                ('A2', '10', 'SAE', '10', '1.5'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A2', '20', 'DRH', '15', '5'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan,t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A2', '30', 'QPR', '12', '1'))

    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A3', '10', 'SAE', '8', '2'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A3', '20', 'DRH', '10', '7'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A3', '30', 'QPR', '5', '1.25'))

    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A4', '10', 'SAE', '10', '1'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A4', '20', 'DRH', '15', '4.6'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A4', '30', 'QPR', '10', '1'))


    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A5', '10', 'DRH', '15', '8.9'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A5', '20', 'HAE', '30', '4'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A5', '30', 'QPR', '10', '1.5'))

    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A6', '10', 'DRH', '10', '5'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A6', '20', 'FRA', '20', '3'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A6', '30', 'HAE', '10', '3'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A6', '40', 'QPR', '10', '1.5'))

    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A7', '10', 'SAE', '10', '5'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A7', '20', 'DRH', '10', '15.5'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A7', '30', 'QPR', '15', '1'))

    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A8', '10', 'SAE', '10', '2'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A8', '20', 'FRA', '20', '3'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A8', '30', 'HAE', '20', '2.5'))
    cursor.execute('INSERT INTO arbeitsplaene (id, nr, bmg, r_plan, t_plan) VALUES (?, ?, ?, ?, ?)', 
                ('A8', '40', 'QPR', '5', '1.2'))

    # Fertigungsplätze
    cursor.executemany('insert into betriebsmittel (bmg, bezeichnung, knoten) values (?,?,?)',
                    [
                    ('RTL', 'Rohteillager', 'a'),
                    ('SAE', 'Zuschnitt', 'b'),
                    ('DRH1', 'Drehen Nr. 1', 'c'),
                    ('DRH2', 'Drehen Nr. 2', 'c'),
                    ('FRA', 'Fräsen', 'd'),
                    ('QPR', 'Qualitätsprüfung', 'e'),
                    ('FTL', 'Fertigteillager', 'f'),
                    ('HAE', 'Härteofen', 'h'),
                    ])

    # FFZ
    cursor.execute('INSERT INTO ffz (id, speed, akkukapazitaet) VALUES (?, ?, ?)', ('F1', '1', '2000'))
    cursor.execute('INSERT INTO ffz (id, speed, akkukapazitaet) VALUES (?, ?, ?)', ('F2', '1.5', '1500'))
    cursor.execute('INSERT INTO ffz (id, speed, akkukapazitaet) VALUES (?, ?, ?)', ('F3', '1.3', '1300'))



    # Änderungen speichern
    conn.commit()

    # Verbindung schließen
    conn.close()