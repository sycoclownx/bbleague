import csv
import os
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(filename='import_csv.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Connect to your PostgreSQL database
try:
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host='localhost',  # Update the host name if necessary
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
except psycopg2.Error as e:
    logging.error(f"Error connecting to the database: {e}")
    raise

# Update the directory path if necessary
teams_dir = '/opt/stacks/bbleague/teams'

# Get a list of CSV files in the teams directory
csv_files = [f for f in os.listdir(teams_dir) if f.endswith('.csv')]

for csv_file in csv_files:
    team_name = os.path.splitext(csv_file)[0]
    csv_path = os.path.join(teams_dir, csv_file)

    # Read the CSV file and get the headers
    with open(csv_path, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)

    # Replace spaces in headers with underscores
    sanitized_headers = [header.replace(' ', '_') for header in headers]

    # Create a new table for the team with default TEXT type for each column
    try:
        columns_with_types = [sql.SQL("{} TEXT").format(sql.Identifier(header)) for header in sanitized_headers]
        create_table_query = sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(team_name),
            sql.SQL(", ").join(columns_with_types)
        )
        cur.execute(create_table_query)
        logging.info(f"Created table for {team_name}")
    except psycopg2.Error as e:
        logging.error(f"Error creating table for {team_name}: {e}")
        continue

    # Insert player data into the table
    try:
        copy_query = sql.SQL("COPY {} FROM STDIN WITH CSV HEADER").format(sql.Identifier(team_name))
        with open(csv_path, 'r') as f:
            cur.copy_expert(copy_query, f)
        logging.info(f"Inserted data into table for {team_name}")
    except psycopg2.Error as e:
        logging.error(f"Error inserting data into table for {team_name}: {e}")
        continue

    # Commit the changes
    try:
        conn.commit()
        logging.info(f"Committed changes for {team_name}")
    except psycopg2.Error as e:
        logging.error(f"Error committing changes for {team_name}: {e}")

# Close the database connection
try:
    cur.close()
    conn.close()
    logging.info("Database connection closed")
except psycopg2.Error as e:
    logging.error(f"Error closing the database connection: {e}")

logging.info("Import process completed")
