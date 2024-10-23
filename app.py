import logging
import random
import os
import traceback
import time
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT')
    )

def create_database():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            team TEXT NOT NULL,
            games_won INTEGER DEFAULT 0,
            games_lost INTEGER DEFAULT 0,
            games_tied INTEGER DEFAULT 0,
            rounds_played INTEGER DEFAULT 0
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS pairings (
            id SERIAL PRIMARY KEY,
            player1_id INTEGER REFERENCES players(id),
            player2_id INTEGER REFERENCES players(id),
            round_number INTEGER,
            result TEXT
        )
        ''')
        conn.commit()

def get_current_round_number():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(round_number) FROM pairings")
        current_round = cursor.fetchone()[0] or 0  # Default to 0 if no rounds exist
    return current_round

def has_played_against(player1_id, player2_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM pairings WHERE (player1_id = %s AND player2_id = %s) OR (player1_id = %s AND player2_id = %s)", 
                       (player1_id, player2_id, player2_id, player1_id))
        played_count = cursor.fetchone()[0]
    return played_count > 0

def add_player(name, team):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO players (name, team) VALUES (%s, %s)', (name, team))
        conn.commit()

def save_pairing(player1_id, player2_id, round_number):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        INSERT INTO pairings (player1_id, player2_id, round_number)
        VALUES (%s, %s, %s)
        ''', (player1_id, player2_id, round_number))
        conn.commit()

def update_player_stats(player_id, result):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if result == "win":
        cursor.execute('''
        UPDATE players SET games_won = games_won + 1, 
                          rounds_played = rounds_played + 1 
        WHERE id = ?
        ''', (player_id,))
    elif result == "lose":
        cursor.execute('''
        UPDATE players SET games_lost = games_lost + 1, 
                          rounds_played = rounds_played + 1 
        WHERE id = ?
        ''', (player_id,))
    elif result == "tie":
        cursor.execute('''
        UPDATE players SET games_tied = games_tied + 1, 
                          rounds_played = rounds_played + 1 
        WHERE id = ?
        ''', (player_id,))
    
    conn.commit()
    conn.close()


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/add_player', methods=['GET', 'POST'])
def add_player():
    if request.method == 'POST':
        name = request.form.get('name')
        team = request.form.get('team')

        if name and team:
            add_player_to_db(name, team)  # This function will be defined next
            return redirect(url_for('players'))  # Redirect to the players list

    return render_template('add_player.html')
    
def add_player_to_db(name, team):
    conn = get_connection()
    with conn:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO players (name, team) VALUES (%s, %s)', (name, team))

@app.route('/players')
def players():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM players")
        players = cursor.fetchall()
    return render_template('players.html', players=players)

@app.route('/pairings', methods=['GET', 'POST'])
def generate_pairings():
    with get_connection() as conn:
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute("SELECT id, name FROM players")
            players = cursor.fetchall()
            return render_template('pairings.html', players=players)

        round_number = get_current_round_number() + 1
        player_requests = {}

        cursor.execute("SELECT id FROM players")
        players = cursor.fetchall()

        for player in players:
            player_id = player[0]
            games_requested = request.form.get(f'games_requested_{player_id}', 0, type=int)
            player_requests[player_id] = games_requested

        cursor.execute("SELECT player1_id, player2_id FROM pairings WHERE round_number IN (%s, %s)", (round_number - 1, round_number - 2))
        existing_pairings = cursor.fetchall()
        existing_pairs_set = {(min(player1, player2), max(player1, player2)) for player1, player2 in existing_pairings}

        pairings = []
        paired_players = set()

        def attempt_pair(player_id, possible_opponents):
            for opponent_id in possible_opponents:
                if player_id != opponent_id and opponent_id not in paired_players and (min(player_id, opponent_id), max(player_id, opponent_id)) not in existing_pairs_set:
                    return opponent_id
            return None

        while True:
            remaining_players = [p for p in player_requests if player_requests[p] > 0]
            random.shuffle(remaining_players)

            if len(remaining_players) < 2:
                break

            paired_this_round = False
            for player in remaining_players:
                while player_requests[player] > 0:
                    opponent = attempt_pair(player, remaining_players)
                    if opponent:
                        pairings.append((player, opponent))
                        paired_players.add(player)
                        paired_players.add(opponent)
                        player_requests[player] -= 1
                        player_requests[opponent] -= 1
                        paired_this_round = True
                    else:
                        break

            if not paired_this_round:
                break

            paired_players.clear()

        for player1, player2 in pairings:
            save_pairing(player1, player2, round_number)

        return redirect('/current_pairings')

@app.route('/current_pairings')
def current_pairings():
    with get_connection() as conn:
        cursor = conn.cursor()

        round_number = get_current_round_number()
        cursor.execute("SELECT player1_id, player2_id FROM pairings WHERE round_number = %s", (round_number,))
        pairings = cursor.fetchall()

        cursor.execute("SELECT id, name FROM players")
        player_names = {row[0]: row[1] for row in cursor.fetchall()}

    pairings_with_names = [(player_names[player1], player_names[player2]) for player1, player2 in pairings if player1 in player_names and player2 in player_names]

    return render_template('current_pairings.html', pairings=pairings_with_names, round_number=round_number)

@app.route('/submit_results', methods=['GET', 'POST'])
def submit_results():
    if request.method == 'POST':
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute('''
                SELECT pairing.id, pairing.player1_id, pairing.player2_id
                FROM pairings pairing
                WHERE pairing.round_number = (SELECT MAX(round_number) FROM pairings)
                ''')
                pairings = cursor.fetchall()

                for pairing in pairings:
                    pairing_id = pairing[0]
                    player1_id = pairing[1]
                    player2_id = pairing[2]
                    result = request.form.get(f'result_{pairing_id}')

                    if result:
                        if result == "tie":
                            cursor.execute('''
                            UPDATE pairings SET result = %s WHERE id = %s
                            ''', ("tie", pairing_id))
                            update_player_stats(player1_id, "tie")
                            update_player_stats(player2_id, "tie")
                        else:
                            winner_id = player1_id if result == "player1" else player2_id
                            loser_id = player2_id if result == "player1" else player1_id
                            
                            cursor.execute('''
                            UPDATE pairings SET result = %s WHERE id = %s
                            ''', ("win" if result == "player1" else "lose", pairing_id))
                            
                            update_player_stats(winner_id, "win")
                            update_player_stats(loser_id, "lose")

                conn.commit()
            return redirect(url_for('home'))

        except Exception as e:
            logging.error(f"Error occurred while submitting results: {e}")
            return "An error occurred while submitting the results. Please try again later."

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
        SELECT p1.name AS player1_name, p2.name AS player2_name, pairing.id
        FROM pairings pairing
        JOIN players p1 ON pairing.player1_id = p1.id
        JOIN players p2 ON pairing.player2_id = p2.id
        WHERE pairing.round_number = (SELECT MAX(round_number) FROM pairings)
        ''')
        pairings = cursor.fetchall()

    return render_template('submit_results.html', pairings=pairings)

if __name__ == "__main__":
    create_database()
    app.run(debug=True, host='0.0.0.0', port=5000)  # Allow external access
