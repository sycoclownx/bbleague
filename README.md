# Blood Bowl League Manager

## Overview
This Flask web application manages pairings for a Blood Bowl league, based on recommendations by Both Down Podcast. It allows league administrators to add players, generate game pairings, and track player statistics.

## Features
- Player management: Add new players with their team information
- Pairing generation: Create game pairings based on player availability and previous matchups
- Round tracking: Automatically manage league rounds
- Player statistics: Track wins, losses, and ties for each player
- Current pairings view: Display the latest round's pairings

## Prerequisites
- Python 3.7+
- PostgreSQL database
- Docker (optional, for containerized deployment)

## Installation

### Local Setup
1. Clone the repository

2. Create a virtual environment and activate it

3. Install the required packages

4. Set up your environment variables:
- Copy the `.env.example` file to `.env`
- Edit the `.env` file and replace the placeholders with your actual database credentials

5. Initialize the database

### Docker Setup
1. Download contents of git to your local machine.
2. Build the Docker image:
docker run -d \
  --name bbleague \
  -p 5000:5000 \
  -e FLASK_APP=app.py \
  -e FLASK_ENV=development \
  -v $(pwd):/app \
  bbleague:latest

### Using Docker Compose
1. Install Docker and Docker Compose.
2. Build the Docker images:
docker-compose build

3. Start the application:
docker-compose up -d

## Usage
1. Start the application:
Or if using Docker:
Start docker container
2. Open a web browser and navigate to `http://localhost:5000`

3. Use the web interface to:
- Add new players
- Generate pairings for a new round
- View current pairings and player statistics

## Project Structure
- `app.py`: Main application file containing route definitions and core logic
- `templates/`: HTML templates for the web interface
- `static/`: CSS and other static files
- `data/`: Database-related files
- `Dockerfile` and `docker-compose.yml`: Files for Docker deployment

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License
This project is licensed under the GNU General Public License v3.0 (GPL-3.0).

GNU GPL v3.0 is a strong copyleft license that requires developers who use or modify this software to make their code available under the same terms. This ensures that the software and its derivatives remain free and open source.

Key points of the GPL-3.0:
- You can use, modify, and distribute this software freely.
- If you distribute modified versions, you must make your modifications available under GPL-3.0.
- You must include the original copyright notice and license text.
- There's no warranty for the program, to the extent permitted by applicable law.

For more details, see the [GNU GPL v3.0 full text](https://www.gnu.org/licenses/gpl-3.0.en.html).
## Acknowledgements
- Both Down Podcast for the league management recommendations
- Flask and its extensions for web framework capabilities
- PostgreSQL for robust data storage
