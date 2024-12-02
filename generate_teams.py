import os
from dotenv import load_dotenv
import psycopg2
from psycopg2 import sql

# Load environment variables from .env file
load_dotenv()

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host='localhost',  # Update the host name if necessary
    port=os.getenv("DB_PORT")
)
cur = conn.cursor()

# Get the names of all tables in the database
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
table_names = [row[0] for row in cur.fetchall()]

# Exclude the players, teams, and pairings tables
excluded_tables = ['players', 'teams', 'pairings']
table_names = [table_name for table_name in table_names if table_name not in excluded_tables]
# Iterate through each table and check if it has the required row
for table_name in table_names:
    # Use sql.Identifier for the table and column names
    query = sql.SQL("SELECT * FROM {} WHERE {} LIKE %s OR {} LIKE %s").format(
        sql.Identifier(table_name),
        sql.Identifier('Skills_and_Traits'),  # Ensure this matches your actual column name
        sql.Identifier('Skills_and_Traits')
    )
    try:
        cur.execute(query, ("%Apothecary: Yes%", "%Apothecary: No%"))
        rows = cur.fetchall()

        if rows:
            # Determine the apothecary status based on the row value
            apothecary = "Yes" if "Apothecary: Yes" in rows[0][1] else "No"

            # Insert a new row into the "teams" table
            cur.execute(sql.SQL("INSERT INTO teams (team, apothecary) VALUES (%s, %s)"), (table_name, apothecary))
            conn.commit()
            print(f"Added row for table: {table_name}")
    except psycopg2.errors.UndefinedColumn as e:
        print(f"Error with table {table_name}: {e}")

# Close the database connection
cur.close()
conn.close()
