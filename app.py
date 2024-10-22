import logging
import random
from flask import Flask, render_template, request, redirect, url_for
import sqlite3

# Set up basic logging; uncomment to turn on error logging
#logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Function to create the database (if needed)
def create_database():
    conn = sqlite3.connect('league.db')
    cursor = conn.cursor()

    # Create players table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        team TEXT NOT NULL,
        games_played INTEGER DEFAULT 0,
        games_won INTEGER DEFAULT 0,
        games_lost INTEGER DEFAULT 0,
        games_tied INTEGER DEFAULT 0,
        rounds_played INTEGER DEFAULT 0
    )
    ''')

    # Create pairings table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pairings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player1_id INTEGER,
        player2_id INTEGER,
        round_number INTEGER,
        result TEXT,
        FOREIGN KEY (player1_id) REFERENCES players(id),
        FOREIGN KEY (player2_id) REFERENCES players(id)
    )
    ''')

    conn.commit()
    conn.close()
    
def get_current_round_number():
    conn = sqlite3.connect('league.db')
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(round_number) FROM pairings")
    current_round = cursor.fetchone()[0] or 0  # Default to 0 if no rounds exist
    conn.close()
    return current_round

def has_played_against(player1_id, player2_id):
    conn = sqlite3.connect('league.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM pairings WHERE (player1_id = ? AND player2_id = ?) OR (player1_id = ? AND player2_id = ?)", 
                   (player1_id, player2_id, player2_id, player1_id))
    played_count = cursor.fetchone()[0]
    conn.close()
    return played_count > 0

def add_player(name, team):
    conn = sqlite3.connect('league.db')
    c = conn.cursor()
    c.execute('INSERT INTO players (name, team) VALUES (?, ?)', (name, team))
    conn.commit()
    conn.close()

def save_pairing(player1_id, player2_id, round_number):
    conn = sqlite3.connect('league.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO pairings (player1_id, player2_id, round_number)
    VALUES (?, ?, ?)
    ''', (player1_id, player2_id, round_number))
    conn.commit()
    conn.close()

def update_player_stats(player_id, result):
    conn = sqlite3.connect('league.db')
    cursor = conn.cursor()
    
    if result == "win":
        cursor.execute('''
        UPDATE players SET games_played = games_played + 1, 
                          games_won = games_won + 1, 
                          rounds_played = rounds_played + 1 
        WHERE id = ?
        ''', (player_id,))
    elif result == "lose":
        cursor.execute('''
        UPDATE players SET games_played = games_played + 1, 
                          games_lost = games_lost + 1, 
                          rounds_played = rounds_played + 1 
        WHERE id = ?
        ''', (player_id,))
    elif result == "tie":
        cursor.execute('''
        UPDATE players SET games_played = games_played + 1, 
                          games_tied = games_tied + 1, 
                          rounds_played = rounds_played + 1 
        WHERE id = ?
        ''', (player_id,))
    
    conn.commit()
    conn.close()
    
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/players')
def players():
    conn = sqlite3.connect('league.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players")
    players = cursor.fetchall()
    conn.close()
    print("Fetching players...")
    return render_template('players.html', players=players)

@app.route('/pairings', methods=['GET', 'POST'])
def generate_pairings():
    with sqlite3.connect('league.db') as conn:
        cursor = conn.cursor()

        if request.method == 'GET':
            cursor.execute("SELECT id, name FROM players")
            players = cursor.fetchall()
            return render_template('pairings.html', players=players)

        # Handle the POST request
        round_number = get_current_round_number() + 1  # Increment to the next round
        player_requests = {}

        # Collect player requests
        cursor.execute("SELECT id FROM players")
        players = cursor.fetchall()

        for player in players:
            player_id = player[0]
            games_requested = request.form.get(f'games_requested_{player_id}', 0, type=int)
            player_requests[player_id] = games_requested

        # Check existing pairings in the current and previous round
        cursor.execute("SELECT player1_id, player2_id FROM pairings WHERE round_number IN (?, ?)", (round_number - 1, round_number - 2))
        existing_pairings = cursor.fetchall()
        existing_pairs_set = {(min(player1, player2), max(player1, player2)) for player1, player2 in existing_pairings}

        # Initialize pairing tracking
        pairings = []
        paired_players = set()

        # Prepare requests and excess tracking
        limited_requests = {}
        excess_requests = {}

        for player_id, requested_games in player_requests.items():
            if requested_games > 2:
                limited_requests[player_id] = 2
                excess_requests[player_id] = requested_games - 2
            else:
                limited_requests[player_id] = requested_games

        # Function to attempt pairing
        def attempt_pair(player_id, possible_opponents):
            for opponent_id in possible_opponents:
                if player_id != opponent_id and opponent_id not in paired_players and (min(player_id, opponent_id), max(player_id, opponent_id)) not in existing_pairs_set:
                    return opponent_id
            return None

        # Pair players who have limited requests (max 2 games)
        while True:
            remaining_players = [p for p in limited_requests if limited_requests[p] > 0]
            random.shuffle(remaining_players)

            if len(remaining_players) < 2:
                break  # Stop if fewer than 2 players are left wanting games

            paired_this_round = False
            for player in remaining_players:
                while limited_requests[player] > 0:
                    opponent = attempt_pair(player, remaining_players)
                    if opponent:
                        pairings.append((player, opponent))
                        paired_players.add(player)
                        paired_players.add(opponent)
                        limited_requests[player] -= 1
                        limited_requests[opponent] -= 1
                        paired_this_round = True
                    else:
                        break  # No more pairs can be formed

            # If no players were paired in this round, exit the loop
            if not paired_this_round:
                break

            # Reset paired players for the next round of pairing
            paired_players.clear()

        # Pair players who have excess requests (after their 2 games)
        remaining_excess_requests = {k: v for k, v in excess_requests.items() if v > 0}

        while True:
            remaining_excess_players = [p for p in remaining_excess_requests if remaining_excess_requests[p] > 0]
            random.shuffle(remaining_excess_players)

            if len(remaining_excess_players) < 2:
                break  # Stop if fewer than 2 players are left wanting games

            paired_this_round = False
            for player in remaining_excess_players:
                while remaining_excess_requests[player] > 0:
                    opponent = attempt_pair(player, remaining_excess_players)
                    if opponent:
                        pairings.append((player, opponent))
                        paired_players.add(player)
                        paired_players.add(opponent)
                        remaining_excess_requests[player] -= 1
                        remaining_excess_requests[opponent] -= 1
                        paired_this_round = True
                    else:
                        break  # No more pairs can be formed

            # If no players were paired in this round, exit the loop
            if not paired_this_round:
                break

            # Reset paired players for the next round of pairing
            paired_players.clear()

        # Insert the pairings into the database
        for player1, player2 in pairings:
            cursor.execute("INSERT INTO pairings (player1_id, player2_id, round_number) VALUES (?, ?, ?)",
                           (player1, player2, round_number))

        conn.commit()
        return redirect('/current_pairings')  # Redirect to the current pairings page after generating

        
@app.route('/current_pairings')
def current_pairings():
    conn = sqlite3.connect('league.db')
    cursor = conn.cursor()

    # Get the current round number
    round_number = get_current_round_number()

    # Fetch pairings for the current round
    cursor.execute("SELECT id, player1_id, player2_id FROM pairings WHERE round_number = ?", (round_number,))
    pairings = cursor.fetchall()

    # Count the number of games that haven't had reported results
    cursor.execute("SELECT COUNT(*) FROM pairings WHERE round_number = ? AND result IS NULL", (round_number,))
    unreported_count = cursor.fetchone()[0]

    # Total games scheduled for the current round
    total_scheduled = len(pairings)

    # Fetch player names and store them in a dictionary
    player_names = {}
    cursor.execute("SELECT id, name FROM players")
    for row in cursor.fetchall():
        player_names[row[0]] = row[1]

    conn.close()

    # Prepare pairings with names and IDs
    pairings_with_names = [(pairing[0], player_names[pairing[1]], player_names[pairing[2]]) for pairing in pairings if pairing[1] in player_names and pairing[2] in player_names]

    return render_template('current_pairings.html', 
                           pairings=pairings_with_names, 
                           round_number=round_number,
                           unreported_count=unreported_count,
                           total_scheduled=total_scheduled)



@app.route('/submit_results', methods=['GET', 'POST'])
def submit_results():
    if request.method == 'POST':
        # Handle results submission
        conn = sqlite3.connect('league.db')
        cursor = conn.cursor()

        # Fetch all current pairings for the current round
        cursor.execute('''
        SELECT pairing.id, pairing.player1_id, pairing.player2_id
        FROM pairings pairing
        WHERE pairing.round_number = (SELECT MAX(round_number) FROM pairings)
        ''')
        pairings = cursor.fetchall()

        # Iterate over each pairing to get results
        for pairing in pairings:
            pairing_id = pairing[0]
            player1_id = pairing[1]
            player2_id = pairing[2]
            result = request.form.get(f'result_{pairing_id}')  # Adjust naming to match
            if result:
                cursor.execute('''
                UPDATE pairings SET result = ? WHERE id = ?
                ''', (result, pairing_id))
                # Update player stats
                update_player_stats(player1_id, result)
                # Update the opponent's stats
                if result == "win":
                    update_player_stats(player2_id, "lose")
                elif result == "lose":
                    update_player_stats(player2_id, "win")
                elif result == "tie":
                    update_player_stats(player2_id, "tie")

        conn.commit()
        conn.close()
        return redirect(url_for('home'))

    # Fetch pairings from the database for display
    conn = sqlite3.connect('league.db')
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p1.name AS player1_name, p2.name AS player2_name, pairing.id
    FROM pairings pairing
    JOIN players p1 ON pairing.player1_id = p1.id
    JOIN players p2 ON pairing.player2_id = p2.id
    WHERE pairing.round_number = (SELECT MAX(round_number) FROM pairings)
    ''')
    pairings = cursor.fetchall()
    conn.close()

    return render_template('submit_results.html', pairings=pairings)

if __name__ == "__main__":
    create_database()
#    add_player('Player 1', 'Team 1')
#    add_player('Player 2', 'Team 2')
#    add_player('Player 3', 'Team 3')
#    add_player('Player 4', 'Team 4')
#    add_player('Player 5', 'Team 5')
#    add_player('Player 6', 'Team 6')
#    add_player('Player 7', 'Team 7')
#    add_player('Player 8', 'Team 8')
    app.run(host='0.0.0.0', port=5000)  # Allow external access
