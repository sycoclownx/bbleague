import logging
import random
import os
import traceback
import time
from flask import Flask, render_template, request, redirect, url_for, current_app
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
    with get_connection() as conn:
        with conn.cursor() as cursor:
            if result == "win":
                cursor.execute('''
                UPDATE players SET games_won = games_won + 1, 
                                  rounds_played = rounds_played + 1 
                WHERE id = %s
                ''', (player_id,))
            elif result == "lose":
                cursor.execute('''
                UPDATE players SET games_lost = games_lost + 1, 
                                  rounds_played = rounds_played + 1 
                WHERE id = %s
                ''', (player_id,))
            elif result == "tie":
                cursor.execute('''
                UPDATE players SET games_tied = games_tied + 1, 
                                  rounds_played = rounds_played + 1 
                WHERE id = %s
                ''', (player_id,))
            conn.commit()


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

from flask import Flask, render_template, request, redirect, url_for, current_app
import random
import traceback

@app.route('/pairings', methods=['GET', 'POST'])
def generate_pairings():
    if request.method == 'GET':
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM players")
            players = cursor.fetchall()
        return render_template('pairing_input.html', players=players)
    elif request.method == 'POST':
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                round_number = get_current_round_number() + 1
                player_requests = {}
                max_games_per_player = 5

                cursor.execute("SELECT id FROM players")
                players = [player[0] for player in cursor.fetchall()]

                total_games_requested = 0
                for player_id in players:
                    games_requested = min(int(request.form.get(f'{player_id}', 0)), max_games_per_player)
                    player_requests[player_id] = games_requested
                    total_games_requested += games_requested

                # Get pairings for the current round
                cursor.execute("SELECT player1_id, player2_id FROM pairings WHERE round_number = %s", (round_number,))
                current_round_pairings = set(tuple(sorted(pair)) for pair in cursor.fetchall())

                # Get all previous pairings
                cursor.execute("SELECT player1_id, player2_id FROM pairings")
                all_previous_pairings = set(tuple(sorted(pair)) for pair in cursor.fetchall())
                pairings = []
                games_scheduled = {player_id: 0 for player_id in player_requests}

                def can_pair(player1, player2):
                    return (
                        player1 != player2 and
                        (player1, player2) not in current_round_pairings and
                        (player2, player1) not in current_round_pairings and
                        games_scheduled[player1] < player_requests[player1] and
                        games_scheduled[player2] < player_requests[player2]
                    )

                def pair_score(player1, player2):
                    if (min(player1, player2), max(player1, player2)) in all_previous_pairings:
                        return 0  # Lower score if they've played before
                    return 1  # Higher score if they haven't played before

                # First, schedule up to 2 games for each player
                for _ in range(2):
                    available_players = [p for p in players if games_scheduled[p] < min(2, player_requests[p])]
                    random.shuffle(available_players)

                    for i in range(0, len(available_players) - 1, 2):
                        player1, player2 = available_players[i], available_players[i + 1]
                        if can_pair(player1, player2):
                            pairings.append((player1, player2))
                            games_scheduled[player1] += 1
                            games_scheduled[player2] += 1
                            current_round_pairings.add((min(player1, player2), max(player1, player2)))

                # Then, schedule additional games up to 5
                while sum(min(player_requests[p] - games_scheduled[p], max_games_per_player - games_scheduled[p]) for p in players) >= 2:
                    available_players = [p for p in players if games_scheduled[p] < min(player_requests[p], max_games_per_player)]
                    if len(available_players) < 2:
                        break

                    available_players.sort(key=lambda p: (player_requests[p] - games_scheduled[p]), reverse=True)
                    paired = False
                    for player1 in available_players:
                        possible_pairs = [(player1, player2) for player2 in available_players if can_pair(player1, player2)]
                        if possible_pairs:
                            best_pair = max(possible_pairs, key=lambda pair: (pair_score(*pair), player_requests[pair[1]] - games_scheduled[pair[1]]))
                            player1, player2 = best_pair
                            pairings.append((player1, player2))
                            games_scheduled[player1] += 1
                            games_scheduled[player2] += 1
                            current_round_pairings.add((min(player1, player2), max(player1, player2)))
                            paired = True
                            break

                    if not paired:
                        break

                # After generating pairings, fetch player names
                pairings_with_names = []
                total_scheduled = 0
                for player1, player2 in pairings:
                    cursor.execute("SELECT name FROM players WHERE id IN (%s, %s)", (player1, player2))
                    names = cursor.fetchall()
                    pairings_with_names.append((names[0][0], names[1][0], total_scheduled + 1))  # Include pairing ID
                    total_scheduled += 1
                    save_pairing(player1, player2, round_number)

                return render_template('current_pairings.html', 
                                       pairings=pairings_with_names,
                                       round_number=round_number,
                                       total_scheduled=total_scheduled,
                                       total_requested=total_games_requested)

        except Exception as e:
            current_app.logger.error(f"Error in generate_pairings: {str(e)}")
            current_app.logger.error(traceback.format_exc())  # Log the full traceback
            return "An error occurred while generating pairings. Please check the server logs for more information.", 500

@app.route('/current_pairings')
def current_pairings():
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get the latest round number
            cursor.execute("SELECT MAX(round_number) FROM pairings")
            latest_round = cursor.fetchone()[0]

            if latest_round is None:
                return "No pairings have been generated yet.", 404

            # Fetch the pairings for the latest round
            cursor.execute("""
                SELECT p.id, p1.name AS player1_name, p2.name AS player2_name 
                FROM pairings p
                JOIN players p1 ON p.player1_id = p1.id
                JOIN players p2 ON p.player2_id = p2.id
                WHERE p.round_number = %s
            """, (latest_round,))

            pairings = cursor.fetchall()

            # Count total games scheduled
            total_scheduled = len(pairings)

            # For total_requested, we'll need to sum up the requested games from the last pairing generation
            # This is an approximation, as we don't store the requested games per round
            cursor.execute("SELECT SUM(games_won + games_lost + games_tied) FROM players")
            total_requested = cursor.fetchone()[0] or 0

        return render_template('current_pairings.html', 
                               pairings=pairings, 
                               round_number=latest_round,
                               total_scheduled=total_scheduled,
                               total_requested=total_requested)

    except Exception as e:
        current_app.logger.error(f"Error in current_pairings: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return "An error occurred while fetching current pairings. Please check the server logs for more information.", 500

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
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)