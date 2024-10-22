PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    team TEXT NOT NULL,
    games_played INTEGER DEFAULT 0,
    games_won INTEGER DEFAULT 0,
    games_lost INTEGER DEFAULT 0,
    games_tied INTEGER DEFAULT 0,
    rounds_played INTEGER DEFAULT 0
);
INSERT INTO players VALUES(1,'Jake','Boozin for a Brusin',0,0,0,0,0);
INSERT INTO players VALUES(2,'Will','Gnome Mercy',0,0,0,0,0);
INSERT INTO players VALUES(3,'Wilson','Cold Bloody Scabs',0,0,0,0,0);
INSERT INTO players VALUES(4,'Brett','Biguns',0,0,0,0,0);
INSERT INTO players VALUES(5,'Mike','Zarr Fire-Breathers',0,0,0,0,0);
INSERT INTO players VALUES(6,'Nathan','Chittering Crawlers',0,0,0,0,0);
INSERT INTO players VALUES(7,'Nick','Powder Monkeys',0,0,0,0,0);
INSERT INTO players VALUES(8,'Morgan','Nine Inch Flails',0,0,0,0,0);
CREATE TABLE pairings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player1_id INTEGER,
    player2_id INTEGER,
    round_number INTEGER,
    result TEXT,
    FOREIGN KEY (player1_id) REFERENCES players(id),
    FOREIGN KEY (player2_id) REFERENCES players(id)
);
INSERT INTO pairings VALUES(1,5,4,1,'tie');
INSERT INTO pairings VALUES(2,5,3,1,NULL);
INSERT INTO pairings VALUES(3,4,1,1,NULL);
INSERT INTO pairings VALUES(4,3,7,1,NULL);
INSERT INTO pairings VALUES(5,1,8,1,NULL);
INSERT INTO pairings VALUES(6,8,6,1,NULL);
INSERT INTO pairings VALUES(7,6,2,1,NULL);
DELETE FROM sqlite_sequence;
INSERT INTO sqlite_sequence VALUES('players',8);
INSERT INTO sqlite_sequence VALUES('pairings',7);
COMMIT;
